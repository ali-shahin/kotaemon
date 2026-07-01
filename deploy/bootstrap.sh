#!/usr/bin/env bash
# One-time VPS bootstrap for the Kotaemon demo deployment.
# Edit the CONFIG section, then: bash deploy/bootstrap.sh
#
# Requires: hcloud CLI (context "newsflow" authenticated), gh CLI (write access
# to the repo), ssh, git.
set -euo pipefail

# ===== CONFIG — edit before running =================================
DOMAIN=""
OPENAI_API_BASE="https://openrouter.ai/api/v1"
OPENAI_API_KEY=""                  # sk-...  (REQUIRED)
OPENAI_CHAT_MODEL="openai/gpt-4o-mini"
OPENAI_EMBEDDINGS_MODEL="openai/text-embedding-3-large"
COHERE_API_KEY=""                  # optional — enables Cohere reranking if set
GH_REPO="ali-shahin/kotaemon"
SERVER_NAME="kotaemon-demo"
HCLOUD_CONTEXT="newsflow"
HCLOUD_LOCATION="nbg1"
SSH_KEY_PATH="$HOME/.ssh/kotaemon-ci"
DEPLOY_USER="deploy"
# ====================================================================

: "${DOMAIN:?Set DOMAIN in the CONFIG section before running}"
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY in the CONFIG section before running}"
: "${OPENAI_API_BASE:?Set OPENAI_API_BASE in the CONFIG section before running}"

log() { printf '\n▶ %s\n' "$*"; }

# --------------------------------------------------------------------
# 1. SSH keypair (no passphrase — used by CI and initial setup)
# --------------------------------------------------------------------
log "SSH keypair..."
if [ ! -f "$SSH_KEY_PATH" ]; then
  ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N "" -C "kotaemon-ci"
  echo "  Created $SSH_KEY_PATH"
else
  echo "  $SSH_KEY_PATH already exists, reusing."
fi
CI_PUBKEY=$(cat "${SSH_KEY_PATH}.pub")

# --------------------------------------------------------------------
# 2. hcloud: context + SSH key + firewall + server (all idempotent)
# --------------------------------------------------------------------
log "hcloud setup..."
hcloud context use "$HCLOUD_CONTEXT"

hcloud ssh-key create --name kotaemon-ci \
  --public-key-from-file "${SSH_KEY_PATH}.pub" 2>/dev/null \
  || echo "  SSH key kotaemon-ci already exists."

hcloud firewall create --name kotaemon-fw 2>/dev/null \
  || echo "  Firewall kotaemon-fw already exists."
for PORT in 22 80 443; do
  hcloud firewall add-rule kotaemon-fw \
    --direction in --protocol tcp --port "$PORT" \
    --source-ips 0.0.0.0/0 --source-ips ::/0 2>/dev/null || true
done
echo "  Inbound 22/80/443 rules applied."

hcloud server create \
  --name "$SERVER_NAME" \
  --type cx23 \
  --image ubuntu-24.04 \
  --ssh-key kotaemon-ci \
  --firewall kotaemon-fw \
  --location "$HCLOUD_LOCATION" 2>/dev/null \
  || echo "  Server $SERVER_NAME already exists."

SERVER_IP=$(hcloud server describe "$SERVER_NAME" -o format='{{.PublicNet.IPv4.IP}}')
echo "  Server IP: $SERVER_IP"

# --------------------------------------------------------------------
# 3. Wait for SSH (server may still be booting)
# --------------------------------------------------------------------
log "Waiting for SSH on $SERVER_IP (up to ~2 min)..."
for i in $(seq 1 24); do
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
      -i "$SSH_KEY_PATH" root@"$SERVER_IP" exit 2>/dev/null && break
  [ "$i" -eq 24 ] && { echo "ERROR: SSH timed out after 2 min."; exit 1; }
  printf '.'
  sleep 5
done
echo "  SSH ready."

# --------------------------------------------------------------------
# 4. Harden + install Docker + create deploy user (idempotent)
# --------------------------------------------------------------------
log "Installing Docker and hardening server..."
CI_PUBKEY_B64=$(printf '%s' "$CI_PUBKEY" | base64 | tr -d '\n')
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_PATH" \
    root@"$SERVER_IP" bash -s -- "$CI_PUBKEY_B64" "$DEPLOY_USER" <<'SETUP'
set -euo pipefail
CI_PUB=$(printf '%s' "$1" | base64 -d)
DUSER="$2"
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
curl -fsSL https://get.docker.com | sh >/dev/null

# Swap — the box has only ~4 GB RAM and Docling loads torch + layout/table models
# during indexing, which can spike past available RAM. A 4 GB swapfile turns a hard
# OOM kill into slow-but-working indexing. Idempotent.
if ! swapon --show | grep -q '/swapfile'; then
  fallocate -l 4G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=4096
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -qF '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "  4 GB swapfile enabled."
else
  echo "  Swap already present."
fi

id -u "$DUSER" &>/dev/null || useradd -m -s /bin/bash "$DUSER"
usermod -aG docker,sudo "$DUSER"

mkdir -p "/home/$DUSER/.ssh"
grep -qF "$CI_PUB" "/home/$DUSER/.ssh/authorized_keys" 2>/dev/null \
  || echo "$CI_PUB" >> "/home/$DUSER/.ssh/authorized_keys"
chmod 700 "/home/$DUSER/.ssh"
chmod 600 "/home/$DUSER/.ssh/authorized_keys"
chown -R "$DUSER:$DUSER" "/home/$DUSER/.ssh"

apt-get install -y -qq fail2ban ufw
ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw --force enable
sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh 2>/dev/null || systemctl restart sshd

mkdir -p /opt/kotaemon && chown "$DUSER" /opt/kotaemon
echo "  Server hardened."
SETUP

# --------------------------------------------------------------------
# 5. Clone repo as deploy user
# --------------------------------------------------------------------
log "Cloning repository on server..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_PATH" \
    "$DEPLOY_USER@$SERVER_IP" bash -s -- "$GH_REPO" <<'CLONE'
set -euo pipefail
REPO="$1"
[ -d /opt/kotaemon/.git ] || git clone "https://github.com/$REPO.git" /opt/kotaemon
cd /opt/kotaemon
git fetch origin
git checkout demo 2>/dev/null \
  || git checkout -b demo origin/develop 2>/dev/null \
  || git checkout -b demo
echo "  Branch: $(git branch --show-current)"
CLONE

# --------------------------------------------------------------------
# 6. Write /opt/kotaemon/.env (skipped if already present)
# --------------------------------------------------------------------
log "Writing .env on server..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_PATH" \
    "$DEPLOY_USER@$SERVER_IP" bash -s -- \
    "$DOMAIN" "$OPENAI_API_KEY" "$OPENAI_CHAT_MODEL" "$OPENAI_EMBEDDINGS_MODEL" "$OPENAI_API_BASE" "$COHERE_API_KEY" <<'DOTENV'
set -euo pipefail
D="$1" KEY="$2" MODEL="$3" EMB="$4" API_BASE="$5" COHERE="$6"
if [ -f /opt/kotaemon/.env ]; then
  echo "  .env already exists — skipping (delete to regenerate)."
  exit 0
fi
cat > /opt/kotaemon/.env << ENVEOF
KH_DOMAIN=${D}
OPENAI_API_BASE=${API_BASE}
OPENAI_API_KEY=${KEY}
OPENAI_CHAT_MODEL=${MODEL}
OPENAI_EMBEDDINGS_MODEL=${EMB}
ENVEOF
[ -n "$COHERE" ] && echo "COHERE_API_KEY=${COHERE}" >> /opt/kotaemon/.env
chmod 600 /opt/kotaemon/.env
echo "  .env written."
DOTENV

# --------------------------------------------------------------------
# 7. GitHub repository secrets
# --------------------------------------------------------------------
log "Setting GitHub secrets..."
gh secret set VPS_HOST    -R "$GH_REPO" --body "$SERVER_IP"
gh secret set VPS_USER    -R "$GH_REPO" --body "$DEPLOY_USER"
gh secret set VPS_SSH_KEY -R "$GH_REPO" < "$SSH_KEY_PATH"
echo "  VPS_HOST, VPS_USER, VPS_SSH_KEY set on $GH_REPO."

# --------------------------------------------------------------------
# Done — print remaining manual steps
# --------------------------------------------------------------------
GH_USER=$(cut -d/ -f1 <<< "$GH_REPO")
GH_PKG=$(cut -d/ -f2 <<< "$GH_REPO")

printf '\n'
printf '╔══════════════════════════════════════════════════════════════╗\n'
printf '║  ✓ Bootstrap complete!                                       ║\n'
printf '║    Server: %-50s║\n' "$SERVER_IP"
printf '╚══════════════════════════════════════════════════════════════╝\n'
printf '\nThree manual steps left:\n\n'
printf '  1. DNS — add an A record:\n'
printf '       %-20s  →  %s\n\n' "$DOMAIN" "$SERVER_IP"
printf '  2. ghcr pull access — pick one:\n'
printf '       a) Make the package public (recommended for a demo):\n'
printf '          https://github.com/users/%s/packages/container/%s/settings\n' "$GH_USER" "$GH_PKG"
printf '       b) Log in on the VPS with a read-only PAT:\n'
printf '          ssh -i %s %s@%s \\\n' "$SSH_KEY_PATH" "$DEPLOY_USER" "$SERVER_IP"
printf "            'docker login ghcr.io -u %s -p <READ_PAT>'\n\n" "$GH_USER"
printf '  3. Push the demo branch to trigger the first deploy:\n'
printf '       git push -u origin demo\n'
printf '     Watch it:  https://github.com/%s/actions\n\n' "$GH_REPO"
