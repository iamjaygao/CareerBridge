import os

def is_migration_mode():
    return os.environ.get("DJANGO_MIGRATION_MODE") == "1"
