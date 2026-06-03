import os
import environ
env = environ.Env()
DEBUG = env("DEBUG", default="False")

print(f"🐉 DEBUG mode is set to: {DEBUG} 🚸")

if DEBUG == "False":
    from .production import *
else:
    from .development import *
