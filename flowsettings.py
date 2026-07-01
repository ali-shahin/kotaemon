import os
from importlib.metadata import version
from importlib.util import find_spec
from inspect import currentframe, getframeinfo
from pathlib import Path

from decouple import config
from ktem.utils.lang import SUPPORTED_LANGUAGE_MAP
from theflow.settings.default import *  # noqa

cur_frame = currentframe()
if cur_frame is None:
    raise ValueError("Cannot get the current frame.")
this_file = getframeinfo(cur_frame).filename
this_dir = Path(this_file).parent

# change this if your app use a different name
KH_PACKAGE_NAME = "kotaemon_app"

KH_APP_NAME = config("KH_APP_NAME", default="Kotaemon")
KH_APP_VERSION = config("KH_APP_VERSION", None)
if not KH_APP_VERSION:
    try:
        # Caution: This might produce the wrong version
        # https://stackoverflow.com/a/59533071
        KH_APP_VERSION = version(KH_PACKAGE_NAME)
    except Exception:
        KH_APP_VERSION = "local"

KH_GRADIO_SHARE = config("KH_GRADIO_SHARE", default=False, cast=bool)
KH_ENABLE_FIRST_SETUP = config("KH_ENABLE_FIRST_SETUP", default=True, cast=bool)
KH_DEMO_MODE = config("KH_DEMO_MODE", default=False, cast=bool)
KH_OLLAMA_URL = config("KH_OLLAMA_URL", default="http://localhost:11434/v1/")

# App can be ran from anywhere and it's not trivial to decide where to store app data.
# So let's use the same directory as the flowsetting.py file.
KH_APP_DATA_DIR = this_dir / "ktem_app_data"
KH_APP_DATA_EXISTS = KH_APP_DATA_DIR.exists()
KH_APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

# User data directory
KH_USER_DATA_DIR = KH_APP_DATA_DIR / "user_data"
KH_USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

# markdown output directory
KH_MARKDOWN_OUTPUT_DIR = KH_APP_DATA_DIR / "markdown_cache_dir"
KH_MARKDOWN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# chunks output directory
KH_CHUNKS_OUTPUT_DIR = KH_APP_DATA_DIR / "chunks_cache_dir"
KH_CHUNKS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# zip output directory
KH_ZIP_OUTPUT_DIR = KH_APP_DATA_DIR / "zip_cache_dir"
KH_ZIP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# zip input directory
KH_ZIP_INPUT_DIR = KH_APP_DATA_DIR / "zip_cache_dir_in"
KH_ZIP_INPUT_DIR.mkdir(parents=True, exist_ok=True)

# HF models can be big, let's store them in the app data directory so that it's easier
# for users to manage their storage.
# ref: https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache
os.environ["HF_HOME"] = str(KH_APP_DATA_DIR / "huggingface")
os.environ["HF_HUB_CACHE"] = str(KH_APP_DATA_DIR / "huggingface")

# doc directory
KH_DOC_DIR = this_dir / "docs"

KH_MODE = "dev"
KH_SSO_ENABLED = config("KH_SSO_ENABLED", default=False, cast=bool)

KH_FEATURE_CHAT_SUGGESTION = config(
    "KH_FEATURE_CHAT_SUGGESTION", default=False, cast=bool
)
KH_FEATURE_USER_MANAGEMENT = config(
    "KH_FEATURE_USER_MANAGEMENT", default=True, cast=bool
)
KH_USER_CAN_SEE_PUBLIC = None
KH_FEATURE_USER_MANAGEMENT_ADMIN = str(
    config("KH_FEATURE_USER_MANAGEMENT_ADMIN", default="admin")
)
KH_FEATURE_USER_MANAGEMENT_PASSWORD = str(
    config("KH_FEATURE_USER_MANAGEMENT_PASSWORD", default="admin")
)
KH_ENABLE_ALEMBIC = False
KH_DATABASE = f"sqlite:///{KH_USER_DATA_DIR / 'sql.db'}"
KH_FILESTORAGE_PATH = str(KH_USER_DATA_DIR / "files")

FEATURE_MODULES = {
    "provider-openai": ("langchain_openai",),
    "provider-azure": ("langchain_openai", "azure.ai.documentintelligence"),
    "provider-cohere": ("cohere", "langchain_cohere"),
    "provider-google": ("langchain_google_genai",),
    "provider-anthropic": ("langchain_anthropic",),
    "provider-mistral": ("langchain_mistralai",),
    "provider-voyageai": ("voyageai",),
    "provider-ollama": ("langchain_ollama",),
    "embedding-fastembed": ("fastembed",),
    "embedding-huggingface": ("sentence_transformers",),
    "reader-adobe": ("adobe.pdfservices.operation",),
    "reader-azure-di": ("azure.ai.documentintelligence",),
    "reader-docling": ("docling",),
    "reader-paddleocr": ("paddleocr",),
    "reader-unstructured": ("unstructured",),
    "tools-web": ("tavily",),
    "graphrag-light": ("lightrag",),
    "graphrag-ms": ("graphrag",),
    "graphrag-nano": ("nano_graphrag",),
}

FEATURE_EXTRAS = {
    "provider-openai": "kotaemon[provider-openai]",
    "provider-azure": "kotaemon[provider-azure]",
    "provider-cohere": "kotaemon[provider-cohere]",
    "provider-google": "kotaemon[provider-google]",
    "provider-anthropic": "kotaemon[provider-anthropic]",
    "provider-mistral": "kotaemon[provider-mistral]",
    "provider-voyageai": "kotaemon[provider-voyageai]",
    "provider-ollama": "kotaemon[provider-ollama]",
    "embedding-fastembed": "kotaemon[embedding-fastembed]",
    "embedding-huggingface": "kotaemon[embedding-huggingface]",
    "reader-adobe": "pdfservices-sdk",
    "reader-azure-di": "kotaemon[provider-azure]",
    "reader-docling": "kotaemon[reader-docling]",
    "reader-paddleocr": "kotaemon[reader-paddleocr]",
    "reader-unstructured": "kotaemon[reader-unstructured]",
    "tools-web": "kotaemon[tools-web]",
    "graphrag-light": "kotaemon[graphrag-light]",
    "graphrag-ms": "manual install: graphrag<=0.3.6 future",
    "graphrag-nano": "kotaemon[graphrag-nano]",
}

PROFILE_FEATURES: dict[str, set[str]] = {
    "core": set(),
    "ollama": {"provider-ollama"},
    "ollama-docs": {
        "provider-ollama",
        "embedding-fastembed",
        "reader-docling",
        "reader-unstructured",
    },
    "lite": {
        "provider-openai",
        "provider-cohere",
        "provider-google",
        "provider-ollama",
        "provider-voyageai",
    },
    "graphrag-light": {
        "provider-openai",
        "provider-cohere",
        "provider-google",
        "provider-ollama",
        "provider-voyageai",
        "graphrag-light",
    },
    "graphrag-nano": {
        "provider-openai",
        "provider-cohere",
        "provider-google",
        "provider-ollama",
        "provider-voyageai",
        "graphrag-nano",
    },
    "full": set(FEATURE_MODULES),
}


def _csv_config(name: str, default: str = "") -> set[str]:
    value = str(config(name, default=default) or "")
    return {item.strip() for item in value.replace(",", " ").split() if item.strip()}


def _has_module(module: str) -> bool:
    try:
        return find_spec(module) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _env_bool_override(name: str, feature: str, features: set[str]) -> None:
    if name not in os.environ:
        return
    if config(name, default=False, cast=bool):
        features.add(feature)
    else:
        features.discard(feature)


KH_APP_PROFILE = str(config("KH_APP_PROFILE", default="lite")).strip() or "lite"
if KH_APP_PROFILE not in PROFILE_FEATURES:
    KH_APP_PROFILE = "lite"

KH_ENABLE_FEATURES = _csv_config("KH_ENABLE_FEATURES")
KH_DISABLE_FEATURES = _csv_config("KH_DISABLE_FEATURES")
KH_ENABLED_FEATURES = set(PROFILE_FEATURES[KH_APP_PROFILE])
KH_ENABLED_FEATURES.update(KH_ENABLE_FEATURES)
KH_ENABLED_FEATURES.difference_update(KH_DISABLE_FEATURES)

_env_bool_override("USE_LIGHTRAG", "graphrag-light", KH_ENABLED_FEATURES)
_env_bool_override("USE_NANO_GRAPHRAG", "graphrag-nano", KH_ENABLED_FEATURES)
_env_bool_override("USE_MS_GRAPHRAG", "graphrag-ms", KH_ENABLED_FEATURES)

KH_FEATURE_STATUS = {}
for feature, modules in FEATURE_MODULES.items():
    missing = [module for module in modules if not _has_module(module)]
    enabled = feature in KH_ENABLED_FEATURES
    KH_FEATURE_STATUS[feature] = {
        "enabled": enabled,
        "available": enabled and not missing,
        "missing": missing,
        "install": FEATURE_EXTRAS.get(feature, ""),
    }

KH_UNAVAILABLE_FEATURES = {
    feature: status
    for feature, status in KH_FEATURE_STATUS.items()
    if status["enabled"] and not status["available"]
}


def feature_enabled(feature: str) -> bool:
    return feature in KH_ENABLED_FEATURES


def feature_available(feature: str) -> bool:
    return bool(KH_FEATURE_STATUS.get(feature, {}).get("available", False))


KH_WEB_SEARCH_BACKEND = (
    "kotaemon.indices.retrievers.tavily_web_search.WebSearch"
    if feature_available("tools-web")
    else None
)

KH_DOCSTORE = {
    # "__type__": "kotaemon.storages.ElasticsearchDocumentStore",
    # "__type__": "kotaemon.storages.SimpleFileDocumentStore",
    "__type__": "kotaemon.storages.LanceDBDocumentStore",
    "path": str(KH_USER_DATA_DIR / "docstore"),
}
KH_VECTORSTORE = {
    # "__type__": "kotaemon.storages.LanceDBVectorStore",
    "__type__": "kotaemon.storages.ChromaVectorStore",
    # "__type__": "kotaemon.storages.MilvusVectorStore",
    # "__type__": "kotaemon.storages.QdrantVectorStore",
    "path": str(KH_USER_DATA_DIR / "vectorstore"),
}
KH_LLMS = {}
KH_EMBEDDINGS = {}
KH_RERANKINGS = {}

# populate options from enabled and installed features
OPENAI_DEFAULT = "<YOUR_OPENAI_KEY>"
OPENAI_API_KEY = config("OPENAI_API_KEY", default=OPENAI_DEFAULT)
GOOGLE_API_KEY = config("GOOGLE_API_KEY", default="your-key")
IS_OPENAI_DEFAULT = len(OPENAI_API_KEY) > 0 and OPENAI_API_KEY != OPENAI_DEFAULT

if (
    feature_available("provider-azure")
    and config("AZURE_OPENAI_API_KEY", default="")
    and config("AZURE_OPENAI_ENDPOINT", default="")
):
    if config("AZURE_OPENAI_CHAT_DEPLOYMENT", default=""):
        KH_LLMS["azure"] = {
            "spec": {
                "__type__": "kotaemon.llms.AzureChatOpenAI",
                "temperature": 0,
                "azure_endpoint": config("AZURE_OPENAI_ENDPOINT", default=""),
                "api_key": config("AZURE_OPENAI_API_KEY", default=""),
                "api_version": config("OPENAI_API_VERSION", default="")
                or "2024-02-15-preview",
                "azure_deployment": config("AZURE_OPENAI_CHAT_DEPLOYMENT", default=""),
                "timeout": 20,
            },
            "default": False,
        }
    if config("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", default=""):
        KH_EMBEDDINGS["azure"] = {
            "spec": {
                "__type__": "kotaemon.embeddings.AzureOpenAIEmbeddings",
                "azure_endpoint": config("AZURE_OPENAI_ENDPOINT", default=""),
                "api_key": config("AZURE_OPENAI_API_KEY", default=""),
                "api_version": config("OPENAI_API_VERSION", default="")
                or "2024-02-15-preview",
                "azure_deployment": config(
                    "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", default=""
                ),
                "timeout": 10,
            },
            "default": False,
        }

if feature_available("provider-openai") and OPENAI_API_KEY:
    KH_LLMS["openai"] = {
        "spec": {
            "__type__": "kotaemon.llms.ChatOpenAI",
            "temperature": 0,
            "base_url": config("OPENAI_API_BASE", default="")
            or "https://api.openai.com/v1",
            "api_key": OPENAI_API_KEY,
            "model": config("OPENAI_CHAT_MODEL", default="gpt-4o-mini"),
            "timeout": 20,
        },
        "default": IS_OPENAI_DEFAULT,
    }
    KH_EMBEDDINGS["openai"] = {
        "spec": {
            "__type__": "kotaemon.embeddings.OpenAIEmbeddings",
            "base_url": config("OPENAI_API_BASE", default="https://api.openai.com/v1"),
            "api_key": OPENAI_API_KEY,
            "model": config(
                "OPENAI_EMBEDDINGS_MODEL", default="text-embedding-3-large"
            ),
            "timeout": 10,
            "context_length": 8191,
        },
        "default": IS_OPENAI_DEFAULT,
    }

VOYAGE_API_KEY = config("VOYAGE_API_KEY", default="")
if feature_available("provider-voyageai") and VOYAGE_API_KEY:
    KH_EMBEDDINGS["voyageai"] = {
        "spec": {
            "__type__": "kotaemon.embeddings.VoyageAIEmbeddings",
            "api_key": VOYAGE_API_KEY,
            "model": config("VOYAGE_EMBEDDINGS_MODEL", default="voyage-3-large"),
        },
        "default": False,
    }
    KH_RERANKINGS["voyageai"] = {
        "spec": {
            "__type__": "kotaemon.rerankings.VoyageAIReranking",
            "model_name": "rerank-2",
            "api_key": VOYAGE_API_KEY,
        },
        "default": False,
    }

LOCAL_MODEL = config("LOCAL_MODEL", default="")
if feature_available("provider-ollama") and (
    LOCAL_MODEL or KH_APP_PROFILE.startswith("ollama")
):
    KH_LLMS["ollama"] = {
        "spec": {
            "__type__": "kotaemon.llms.ChatOpenAI",
            "base_url": KH_OLLAMA_URL,
            "model": config("LOCAL_MODEL", default="qwen2.5:7b"),
            "api_key": "ollama",
        },
        "default": not IS_OPENAI_DEFAULT,
    }
    KH_LLMS["ollama-long-context"] = {
        "spec": {
            "__type__": "kotaemon.llms.LCOllamaChat",
            "base_url": KH_OLLAMA_URL.replace("v1/", ""),
            "model": config("LOCAL_MODEL", default="qwen2.5:7b"),
            "num_ctx": 8192,
        },
        "default": False,
    }
    KH_EMBEDDINGS["ollama"] = {
        "spec": {
            "__type__": "kotaemon.embeddings.OpenAIEmbeddings",
            "base_url": KH_OLLAMA_URL,
            "model": config("LOCAL_MODEL_EMBEDDINGS", default="nomic-embed-text"),
            "api_key": "ollama",
        },
        "default": not KH_EMBEDDINGS,
    }

if feature_available("embedding-fastembed"):
    KH_EMBEDDINGS["fast_embed"] = {
        "spec": {
            "__type__": "kotaemon.embeddings.FastEmbedEmbeddings",
            "model_name": "BAAI/bge-base-en-v1.5",
        },
        "default": not KH_EMBEDDINGS,
    }

if feature_available("provider-anthropic"):
    KH_LLMS["claude"] = {
        "spec": {
            "__type__": "kotaemon.llms.chats.LCAnthropicChat",
            "model_name": "claude-3-5-sonnet-20240620",
            "api_key": "your-key",
        },
        "default": False,
    }
if feature_available("provider-google"):
    KH_LLMS["google"] = {
        "spec": {
            "__type__": "kotaemon.llms.chats.LCGeminiChat",
            "model_name": "gemini-1.5-flash",
            "api_key": GOOGLE_API_KEY,
        },
        "default": not IS_OPENAI_DEFAULT,
    }
    KH_EMBEDDINGS["google"] = {
        "spec": {
            "__type__": "kotaemon.embeddings.LCGoogleEmbeddings",
            "model": "models/text-embedding-004",
            "google_api_key": GOOGLE_API_KEY,
        },
        "default": not IS_OPENAI_DEFAULT,
    }
if feature_available("provider-openai"):
    KH_LLMS["groq"] = {
        "spec": {
            "__type__": "kotaemon.llms.ChatOpenAI",
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama-3.1-8b-instant",
            "api_key": "your-key",
        },
        "default": False,
    }
if feature_available("provider-cohere"):
    KH_LLMS["cohere"] = {
        "spec": {
            "__type__": "kotaemon.llms.chats.LCCohereChat",
            "model_name": "command-r-plus-08-2024",
            "api_key": config("COHERE_API_KEY", default="your-key"),
        },
        "default": False,
    }
    KH_EMBEDDINGS["cohere"] = {
        "spec": {
            "__type__": "kotaemon.embeddings.LCCohereEmbeddings",
            "model": "embed-multilingual-v3.0",
            "cohere_api_key": config("COHERE_API_KEY", default="your-key"),
            "user_agent": "default",
        },
        "default": False,
    }
    KH_RERANKINGS["cohere"] = {
        "spec": {
            "__type__": "kotaemon.rerankings.CohereReranking",
            "model_name": "rerank-v4.0-fast",
            "cohere_api_key": config("COHERE_API_KEY", default=""),
        },
        "default": True,
    }
if feature_available("provider-mistral"):
    KH_LLMS["mistral"] = {
        "spec": {
            "__type__": "kotaemon.llms.ChatOpenAI",
            "base_url": "https://api.mistral.ai/v1",
            "model": "ministral-8b-latest",
            "api_key": config("MISTRAL_API_KEY", default="your-key"),
        },
        "default": False,
    }
    KH_EMBEDDINGS["mistral"] = {
        "spec": {
            "__type__": "kotaemon.embeddings.LCMistralEmbeddings",
            "model": "mistral-embed",
            "api_key": config("MISTRAL_API_KEY", default="your-key"),
        },
        "default": False,
    }

KH_REASONINGS = [
    "ktem.reasoning.simple.FullQAPipeline",
    "ktem.reasoning.simple.FullDecomposeQAPipeline",
    "ktem.reasoning.react.ReactAgentPipeline",
    "ktem.reasoning.rewoo.RewooAgentPipeline",
]
KH_REASONINGS_USE_MULTIMODAL = config("USE_MULTIMODAL", default=False, cast=bool)
KH_VLM_ENDPOINT = "{0}/openai/deployments/{1}/chat/completions?api-version={2}".format(
    config("AZURE_OPENAI_ENDPOINT", default=""),
    config("OPENAI_VISION_DEPLOYMENT_NAME", default="gpt-4o"),
    config("OPENAI_API_VERSION", default=""),
)


SETTINGS_APP: dict[str, dict] = {}


SETTINGS_REASONING = {
    "use": {
        "name": "Reasoning options",
        "value": None,
        "choices": [],
        "component": "radio",
    },
    "lang": {
        "name": "Language",
        "value": "en",
        "choices": [(lang, code) for code, lang in SUPPORTED_LANGUAGE_MAP.items()],
        "component": "dropdown",
    },
    "max_context_length": {
        "name": "Max context length (LLM)",
        "value": 32000,
        "component": "number",
    },
}

USE_LIGHTRAG = feature_available("graphrag-light")
USE_NANO_GRAPHRAG = feature_available("graphrag-nano")
USE_MS_GRAPHRAG = feature_available("graphrag-ms")
USE_GLOBAL_GRAPHRAG = config(
    "USE_GLOBAL_GRAPHRAG",
    default=USE_LIGHTRAG or USE_NANO_GRAPHRAG or USE_MS_GRAPHRAG,
    cast=bool,
)

GRAPHRAG_INDEX_TYPES = []

if USE_MS_GRAPHRAG:
    GRAPHRAG_INDEX_TYPES.append("ktem.index.file.graph.GraphRAGIndex")
if USE_NANO_GRAPHRAG:
    GRAPHRAG_INDEX_TYPES.append("ktem.index.file.graph.NanoGraphRAGIndex")
if USE_LIGHTRAG:
    GRAPHRAG_INDEX_TYPES.append("ktem.index.file.graph.LightRAGIndex")

KH_GRAPH_BACKENDS = {
    "ms": USE_MS_GRAPHRAG,
    "nano": USE_NANO_GRAPHRAG,
    "light": USE_LIGHTRAG,
}

KH_AVAILABLE_READER_MODES = [
    ("Default (open-source)", "default"),
]
if feature_available("reader-adobe"):
    KH_AVAILABLE_READER_MODES.append(("Adobe API (figure+table extraction)", "adobe"))
if feature_available("reader-azure-di"):
    KH_AVAILABLE_READER_MODES.append(
        ("Azure AI Document Intelligence (figure+table extraction)", "azure-di")
    )
if feature_available("reader-docling"):
    KH_AVAILABLE_READER_MODES.append(("Docling (figure+table extraction)", "docling"))
if feature_available("reader-paddleocr"):
    KH_AVAILABLE_READER_MODES.extend(
        [
            ("PaddleOCR PPStructureV3 (table+figure extraction)", "paddle-struct"),
            ("PaddleOCR-VL (VLM document parsing)", "paddle-vl"),
        ]
    )

KH_DISABLED_READER_MODES = [
    {
        "feature": feature,
        "missing": status["missing"],
        "install": status["install"],
    }
    for feature, status in KH_FEATURE_STATUS.items()
    if feature.startswith("reader-") and status["enabled"] and not status["available"]
]
KH_READER_MODE_CHOICES = [
    *KH_AVAILABLE_READER_MODES,
    *[
        (
            f"Disabled: {item['feature']} (install {item['install']})",
            f"disabled:{item['feature']}",
        )
        for item in KH_DISABLED_READER_MODES
    ],
]

# When Docling is available, route PDFs through it by default (better table/figure
# extraction) than the basic open-source reader, with no manual reader selection.
# Applied via the file-index dev override (see pipelines.py `dev_settings`).
if feature_available("reader-docling"):
    FILE_INDEX_PIPELINE_FILE_EXTRACTORS = {
        ".pdf": "kotaemon.loaders.DoclingReader",
    }

KH_INDEX_TYPES = [
    "ktem.index.file.FileIndex",
    *GRAPHRAG_INDEX_TYPES,
]

GRAPHRAG_INDICES = [
    {
        "name": graph_type.split(".")[-1].replace("Index", "")
        + " Collection",  # get last name
        "config": {
            "supported_file_types": (
                ".png, .jpeg, .jpg, .tiff, .tif, .pdf, .xls, .xlsx, .doc, .docx, "
                ".pptx, .csv, .html, .mhtml, .txt, .md, .zip"
            ),
            "private": True,
        },
        "index_type": graph_type,
    }
    for graph_type in GRAPHRAG_INDEX_TYPES
]

KH_INDICES = [
    {
        "name": "File Collection",
        "config": {
            "supported_file_types": (
                ".png, .jpeg, .jpg, .tiff, .tif, .pdf, .xls, .xlsx, .doc, .docx, "
                ".pptx, .csv, .html, .mhtml, .txt, .md, .zip"
            ),
            "private": True,
        },
        "index_type": "ktem.index.file.FileIndex",
    },
    *GRAPHRAG_INDICES,
]
