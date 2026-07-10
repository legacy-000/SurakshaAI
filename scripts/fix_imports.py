"""Updates imports in suraksha_ai/common/ to use common. prefix instead of functions. prefix."""

import os
import re

COMMON_DIR = os.path.join(os.path.dirname(__file__), "..", "functions", "suraksha_ai", "common")
DEPLOY_MAIN = os.path.join(os.path.dirname(__file__), "..", "functions", "suraksha_ai", "main.py")

REPLACEMENTS = [
    (r"from functions\.(ai|sql|db|chat|evidence|auth|utils|analytics|network|offender|investigation|forecast|cache|health|security|voice|pdf)\.", r"from common.\1."),
    (r"import functions\.(ai|sql|db|chat|evidence|auth|utils|analytics|network|offender|investigation|forecast|cache|health|security|voice|pdf)\.", r"import common.\1."),
    (r"from functions\.main import", r"from common.main_handler import"),
    (r"from models\.", r"from common.models."),
    (r"import models\.", r"import common.models."),
    (r"from config\.", r"from common.config."),
    (r"import config\.", r"import common.config."),
]


def fix_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin-1") as f:
            content = f.read()

    original = content
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    # Fix all files in common/
    fixed = []
    for root, dirs, files in os.walk(COMMON_DIR):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                if fix_file(path):
                    fixed.append(os.path.relpath(path, COMMON_DIR))

    # Create common/main_handler.py (copy of functions/main.py)
    src_main = os.path.join(os.path.dirname(__file__), "..", "functions", "main.py")
    dst_main_handler = os.path.join(COMMON_DIR, "main_handler.py")
    with open(src_main, "r", encoding="utf-8") as f:
        content = f.read()
    # Fix its imports too
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)
    # Also fix _init_catalyst_app import if legacy exists
    if "import zcatalyst_sdk" not in content:
        content = content.replace("from zcatalyst import app as catalyst_app", "import zcatalyst_sdk")
        content = content.replace("import zcatalyst", "import zcatalyst_sdk")
        content = content.replace("app = catalyst_app.initialize()", "app = zcatalyst_sdk.initialize()")
        content = content.replace("zcatalyst.initialize()", "zcatalyst_sdk.initialize()")
    with open(dst_main_handler, "w", encoding="utf-8") as f:
        f.write(content)
    fixed.append("main_handler.py")

    # Update suraksha_ai/main.py to use common package
    if os.path.exists(DEPLOY_MAIN):
        with open(DEPLOY_MAIN, "r", encoding="latin-1") as f:
            deploy_content = f.read()
        deploy_content = deploy_content.replace(
            "from functions.main import SurakshaAIHandler",
            "from common.main_handler import SurakshaAIHandler"
        )
        deploy_content = deploy_content.replace(
            "from models.dto import",
            "from common.models.dto import"
        )
        # Remove sys.path hack since common/ is in the same directory
        deploy_content = re.sub(
            r"sys\.path\.insert\(0, os\.path\.join\(os\.path\.dirname\(__file__\), '\.\.'\)\)\n",
            "",
            deploy_content
        )
        with open(DEPLOY_MAIN, "w", encoding="utf-8") as f:
            f.write(deploy_content)
        fixed.append("suraksha_ai/main.py (updated imports)")

    print(f"Fixed {len(fixed)} files:")
    for f in fixed:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
