# Lite version
FROM python:3.11-slim AS lite

# Common dependencies
RUN apt-get update -qqy && \
    apt-get install -y --no-install-recommends \
        ssh \
        git \
        gcc \
        g++ \
        poppler-utils \
        libpoppler-dev \
        unzip \
        curl \
        cargo \
        && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

# Setup args
ARG TARGETPLATFORM
ARG TARGETARCH
ARG KH_APP_EXTRAS=runtime-lite
ARG KH_APP_PROFILE=lite

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
ENV TARGETARCH=${TARGETARCH}
ENV KH_APP_PROFILE=${KH_APP_PROFILE}
ENV KH_APP_EXTRAS=${KH_APP_EXTRAS}

# Create working directory
WORKDIR /app

# Download pdfjs
COPY scripts/download_pdfjs.sh /app/scripts/download_pdfjs.sh
RUN chmod +x /app/scripts/download_pdfjs.sh
ENV PDFJS_PREBUILT_DIR="/app/libs/ktem/ktem/assets/prebuilt/pdfjs-dist"
RUN bash scripts/download_pdfjs.sh $PDFJS_PREBUILT_DIR

# Install uv dependencies
RUN pip install --no-cache-dir "uv"

# Copy contents
COPY . /app
COPY launch.sh /app/launch.sh
COPY .env.example /app/.env

# Install the base app packages only. Optional extras are installed by later targets.
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv sync --frozen --no-dev --package kotaemon --extra "$KH_APP_EXTRAS" --package ktem --python /usr/local/bin/python \
    && uv pip install --python .venv "pdfservices-sdk@git+https://github.com/niallcm/pdfservices-python-sdk.git@bump-and-unfreeze-requirements"

ENTRYPOINT ["sh", "/app/launch.sh"]

# Full version
FROM lite AS full

ENV KH_APP_PROFILE=full

# Additional dependencies for full version
RUN apt-get update -qqy && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-jpn \
        libsm6 \
        libxext6 \
        libreoffice \
        ffmpeg \
        libmagic-dev \
        && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install torch and torchvision for unstructured
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv pip install --python .venv torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install additional runtime packages for advanced document and retrieval support.
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv pip install --python .venv "libs/kotaemon[runtime-full]" \
    && uv pip install --python .venv unstructured[all-docs]

RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    if [ "$TARGETARCH" = "amd64" ]; then uv pip install --python .venv "graphrag<=0.3.6" future; fi

# Download NLTK data from LlamaIndex
RUN /app/.venv/bin/python -c "from llama_index.core.readers.base import BaseReader"

# Optional RAG: lightRAG
ENV KH_ENABLE_FEATURES=graphrag-light
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv pip install --python .venv "libs/kotaemon[graphrag-light]"

ENTRYPOINT ["sh", "/app/launch.sh"]

# Lite plus the Docling reader for better PDF/table/figure extraction.
# Much lighter than `full` (no unstructured/torchvision/libreoffice) so it fits a
# small VPS. Keeps the lite profile and just enables the docling feature.
FROM lite AS lite-docling

ENV KH_APP_PROFILE=lite
ENV KH_ENABLE_FEATURES=reader-docling
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv pip install --python .venv "libs/kotaemon[reader-docling]"

ENTRYPOINT ["sh", "/app/launch.sh"]

# LightRAG without full document-processing dependencies
FROM lite AS graphrag-light

ENV KH_APP_PROFILE=graphrag-light
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv pip install --python .venv "libs/kotaemon[runtime-graphrag-light]"

ENTRYPOINT ["sh", "/app/launch.sh"]

# Ollama plus enhanced open-source document readers
FROM lite AS ollama-docs

ENV KH_APP_PROFILE=ollama-docs
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv pip install --python .venv "libs/kotaemon[runtime-ollama-docs]"

ENTRYPOINT ["sh", "/app/launch.sh"]

# PaddleOCR version (GPU-only)
FROM full AS paddle

ARG CUDA_VERSION=130

# Install paddlepaddle and paddleocr
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv pip install --python .venv paddlepaddle-gpu==3.3.0 \
        -i "https://www.paddlepaddle.org.cn/packages/stable/cu${CUDA_VERSION}/" \
    && uv pip install --python .venv "libs/kotaemon[reader-paddleocr]"

ENTRYPOINT ["sh", "/app/launch.sh"]

# Ollama-bundled version
FROM lite AS ollama

ENV KH_APP_PROFILE=ollama
RUN --mount=type=ssh  \
    --mount=type=cache,target=/root/.cache/uv  \
    uv pip install --python .venv "libs/kotaemon[runtime-ollama]"

# Install ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# RUN nohup bash -c "ollama serve &" && sleep 4 && ollama pull qwen2.5:7b
RUN nohup bash -c "ollama serve &" && sleep 4 && ollama pull nomic-embed-text

ENTRYPOINT ["sh", "/app/launch.sh"]
