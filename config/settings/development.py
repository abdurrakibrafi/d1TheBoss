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


# Then configure email settings like this:
EMAIL_HOST = env.str('EMAIL_HOST', default='smtp4dev')  # For string values
EMAIL_PORT = env.int('EMAIL_PORT', default=25)          # For integer values
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)  # For boolean values
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='no-reply@example.com')


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
