"""Prepares suraksha_ai function for Catalyst deployment by creating a self-contained common/ package."""

import os
import shutil
import sys

FUNCTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "functions")
TARGET_DIR = os.path.join(FUNCTIONS_DIR, "suraksha_ai", "common")

EXCLUDED = {"__pycache__", "node_modules", ".git", "prompts"}

# Modules to copy into common/
MODULES = [
    "ai", "sql", "db", "chat", "evidence", "auth", "utils",
    "analytics", "network", "offender", "investigation", "forecast",
    "cache", "health", "security", "voice", "pdf",
]

# Models
MODELS_SRC = os.path.join(os.path.dirname(__file__), "..", "models")
MODELS_DST = os.path.join(TARGET_DIR, "models")

# Config
CONFIG_SRC = os.path.join(os.path.dirname(__file__), "..", "config")
CONFIG_DST = os.path.join(TARGET_DIR, "config")

# Prompts (copy into ai/prompts inside common)
PROMPTS_SRC = os.path.join(FUNCTIONS_DIR, "ai", "prompts")


def clean_target():
    if os.path.exists(TARGET_DIR):
        print(f"Cleaning {TARGET_DIR}...")
        shutil.rmtree(TARGET_DIR)


def copy_module(name):
    src = os.path.join(FUNCTIONS_DIR, name)
    dst = os.path.join(TARGET_DIR, name)
    if os.path.isdir(src):
        print(f"  Copying {name}/...")
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*EXCLUDED))
        # Ensure __init__.py exists
        init_file = os.path.join(dst, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()
    else:
        print(f"  Skipping {name} (not a directory)")


def copy_models():
    if os.path.isdir(MODELS_SRC):
        print("  Copying models/...")
        shutil.copytree(MODELS_SRC, MODELS_DST, ignore=shutil.ignore_patterns(*EXCLUDED))
        init_file = os.path.join(MODELS_DST, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()


def copy_config():
    if os.path.isdir(CONFIG_SRC):
        print("  Copying config/...")
        shutil.copytree(CONFIG_SRC, CONFIG_DST, ignore=shutil.ignore_patterns(*EXCLUDED))
        init_file = os.path.join(CONFIG_DST, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()


def copy_prompts():
    ai_dst = os.path.join(TARGET_DIR, "ai", "prompts")
    if os.path.isdir(PROMPTS_SRC):
        print("  Copying ai/prompts/...")
        shutil.copytree(PROMPTS_SRC, ai_dst, ignore=shutil.ignore_patterns(*EXCLUDED))


def ensure_init(directory):
    for root, dirs, files in os.walk(directory):
        if root == directory:
            continue
        if "__init__.py" not in files:
            open(os.path.join(root, "__init__.py"), "a").close()


def main():
    print("Preparing suraksha_ai function for Catalyst deployment...")
    clean_target()
    os.makedirs(TARGET_DIR, exist_ok=True)

    print("\nCopying shared modules:")
    for mod in MODULES:
        copy_module(mod)

    print("\nCopying models:")
    copy_models()

    print("\nCopying config:")
    copy_config()

    print("\nCopying prompts:")
    copy_prompts()

    print("\nEnsuring __init__.py files...")
    ensure_init(TARGET_DIR)

    print("\nDone! suraksha_ai/common/ is ready for deployment.")


if __name__ == "__main__":
    main()
