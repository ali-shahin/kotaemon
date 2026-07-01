# Demo deployment (Hetzner VPS)

Auto-deploys the Kotaemon **lite** image to a Hetzner VPS on every push to the
`demo` branch. CI builds and pushes the image to ghcr, then SSHes into the VPS to
roll the stack. Caddy fronts the app with automatic Let's Encrypt TLS.

## Quick start (automated)

Edit the `CONFIG` section at the top of `deploy/bootstrap.sh` (set `DOMAIN` and
`OPENAI_API_KEY`), then run once from the repo root:

```bash
bash deploy/bootstrap.sh
```

The script creates the SSH keypair, provisions the Hetzner CX22 server (context
**newsflow**), hardens it, clones the repo, writes `.env`, and populates the three
required GitHub secrets. See [manual steps](#one-time-vps-setup) below if you prefer
to provision by hand.

```
push to demo ──▶ GitHub Actions (deploy-demo.yaml)
                   ├─ build lite image (Dockerfile target=lite)
                   ├─ push ghcr.io/ali-shahin/kotaemon:demo-lite (+ :sha-<short>-lite)
                   └─ ssh VPS ▶ git pull + docker compose pull + up -d

Internet ─80/443─▶ Caddy (TLS) ─▶ kotaemon:7860 (internal network)
                                     └─ volume ./ktem_app_data
```

Files in this directory:

- `docker-compose.prod.yml` — pulls the ghcr image and runs it behind Caddy.
- `Caddyfile` — TLS reverse proxy to `kotaemon:7860`.

## One-time VPS setup

1. **Provision** a Hetzner **CX22** (2 vCPU, 4 GB RAM), Ubuntu 24.04, add your SSH key.
2. **Firewall** — attach a Hetzner Cloud Firewall allowing inbound **22, 80, 443** only.
3. **Harden + install Docker** (as root, then as the deploy user):
   ```bash
   adduser deploy && usermod -aG sudo deploy
   curl -fsSL https://get.docker.com | sh
   usermod -aG docker deploy
   apt-get install -y fail2ban
   ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw enable
   # disable SSH password auth in /etc/ssh/sshd_config: PasswordAuthentication no
   ```
4. **Deploy SSH key** — generate a dedicated keypair for CI (no passphrase) and append
   the public key to the deploy user's `~/.ssh/authorized_keys`. The private key goes
   into the `VPS_SSH_KEY` GitHub secret.
5. **Clone the repo** at `/opt/kotaemon`:
   ```bash
   sudo mkdir -p /opt/kotaemon && sudo chown deploy /opt/kotaemon
   git clone https://github.com/ali-shahin/kotaemon.git /opt/kotaemon
   cd /opt/kotaemon && git checkout demo
   ```
6. **Create `/opt/kotaemon/.env`** (git-ignored) — see required keys below.
7. **ghcr pull access** — make the `kotaemon` package public in the fork's GitHub
   Packages settings, **or** run `docker login ghcr.io` on the VPS with a read-only PAT.
8. **DNS** — add an A record for your domain (e.g. `demo.example.com`) → VPS IP.
9. **First boot**:
   ```bash
   cd /opt/kotaemon
   docker compose -f deploy/docker-compose.prod.yml pull
   docker compose -f deploy/docker-compose.prod.yml up -d
   ```

## Required `.env` keys (on the VPS, not committed)

```dotenv
# Domain Caddy issues the TLS cert for
KH_DOMAIN=demo.example.com

# Cloud LLM / embeddings
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDINGS_MODEL=text-embedding-3-large

# Optional: override the ghcr image tag (defaults to demo-lite)
# KOTAEMON_IMAGE=ghcr.io/ali-shahin/kotaemon:demo-lite
```

> The default login is `admin/admin`. The `.env` seed only applies on first DB
> init — log in and change the admin password immediately after the first deploy.

## Required GitHub repository secrets

| Secret        | Value                                                                   |
| ------------- | ----------------------------------------------------------------------- |
| `VPS_HOST`    | VPS public IP                                                           |
| `VPS_USER`    | deploy user (e.g. `deploy`)                                             |
| `VPS_SSH_KEY` | private key whose public half is in the deploy user's `authorized_keys` |

The image push uses the built-in `GITHUB_TOKEN`; no registry secret is needed.

## Operations

- **Logs:** `docker compose -f deploy/docker-compose.prod.yml logs -f kotaemon`
  (use `caddy` to debug cert issuance).
- **Status:** `docker compose -f deploy/docker-compose.prod.yml ps`
- **Rollback:** pin a previous image and restart:
  ```bash
  KOTAEMON_IMAGE=ghcr.io/ali-shahin/kotaemon:sha-<short>-lite \
    docker compose -f deploy/docker-compose.prod.yml up -d
  ```
- **Data:** all app state persists in `/opt/kotaemon/ktem_app_data` — back it up
  (e.g. a nightly tarball to a Hetzner Storage Box).
