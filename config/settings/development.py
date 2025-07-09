from .base import *

print("🔧 Running in DEVELOPMENT mode")

DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Database for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
    }
}

# Email configuration for development
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("DEV_EMAIL_HOST")
EMAIL_HOST_USER = env("DEV_EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("DEV_EMAIL_HOST_PASSWORD")
EMAIL_PORT = env.int("DEV_EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env("DEV_DEFAULT_FROM_EMAIL")

# Redis for development
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://redis:6379/0")],
        },
    },
}

# Development logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
