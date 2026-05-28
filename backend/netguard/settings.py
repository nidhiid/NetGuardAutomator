import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent


def load_env_file(path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env_file(PROJECT_ROOT / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-netguard-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "policies",
    "routes",
    "configs",
    "monitoring",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "netguard.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "netguard.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("POSTGRES_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("POSTGRES_DB", "netguard"),
        "USER": os.environ.get("POSTGRES_USER", "netguard"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "netguard"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5433"),
    }
}

if "test" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ANSIBLE_INVENTORY = os.environ.get("ANSIBLE_INVENTORY", PROJECT_ROOT / "ansible" / "inventory.ini")
ANSIBLE_FIREWALL_PLAYBOOK = os.environ.get(
    "ANSIBLE_FIREWALL_PLAYBOOK",
    PROJECT_ROOT / "ansible" / "playbooks" / "apply_firewall.yml",
)
ANSIBLE_ROUTES_PLAYBOOK = os.environ.get(
    "ANSIBLE_ROUTES_PLAYBOOK",
    PROJECT_ROOT / "ansible" / "playbooks" / "apply_routes.yml",
)
ANSIBLE_ROLLBACK_PLAYBOOK = os.environ.get(
    "ANSIBLE_ROLLBACK_PLAYBOOK",
    PROJECT_ROOT / "ansible" / "playbooks" / "rollback_config.yml",
)
ANSIBLE_RUNTIME_DIR = os.environ.get("ANSIBLE_RUNTIME_DIR", PROJECT_ROOT / "ansible" / "generated")

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}
