"""Build the Catalyst function bundle.

Catalyst's console upload takes the zip as-is and never runs pip, so the
third-party deps are cross-downloaded as linux/cp313 wheels and vendored in.
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

SRC = "functions/suraksha_api"
OUT = "functions/suraksha_api_bundle.zip"
VENDOR = os.path.join(SRC, "vendor")

if "--skip-pip" not in sys.argv:
    shutil.rmtree(VENDOR, ignore_errors=True)
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "--target", VENDOR,
        "--platform", "manylinux2014_x86_64",
        "--python-version", "3.13",
        "--only-binary=:all:", "--no-compile", "-q",
        "-r", os.path.join(SRC, "requirements.txt"),
    ], check=True)
    # pip drops host-platform console scripts and headers in; useless on linux
    for junk in ("bin", "include", "Scripts"):
        shutil.rmtree(os.path.join(VENDOR, junk), ignore_errors=True)

if os.path.exists(OUT):
    os.remove(OUT)

SKIP_DIRS = {"__pycache__", ".git"}


def add_tree(z, root, prefix):
    n = 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".pyc", ".pyo")) or f == ".env":
                continue
            p = os.path.join(dirpath, f)
            arc = prefix + os.path.relpath(p, root).replace(os.sep, "/")
            z.write(p, arc)
            n += 1
    return n


def build_config():
    """catalyst-config.json with credentials injected from .env.

    Catalyst has no console UI for function env variables — they come from
    deployment.env_variables at deploy time. Injecting here keeps the secrets
    out of the tracked source config; the zip itself is gitignored.
    """
    with open(os.path.join(SRC, "catalyst-config.json")) as fh:
        cfg = json.load(fh)

    wanted = ("CATALYST_CLIENT_ID", "CATALYST_CLIENT_SECRET",
              "CATALYST_REFRESH_TOKEN", "CATALYST_DC", "CATALYST_PROJECT_ID",
              "USE_CATALYST", "LLM_PROVIDER", "CORS_ORIGINS",
              "GLM_ENDPOINT_URL", "GLM_MODEL_ID",
              "EVIDENCE_FOLDER_ID", "WITNESS_FOLDER_ID",
              "CHAT_UPLOADS_FOLDER_ID", "QUICKML_ENDPOINT_KEY")
    env = {}
    if os.path.exists(".env"):
        with open(".env") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k in wanted and v:
                    env[k] = v

    cfg.setdefault("deployment", {})["env_variables"] = env
    missing = [k for k in ("CATALYST_CLIENT_ID", "CATALYST_CLIENT_SECRET",
                           "CATALYST_REFRESH_TOKEN") if k not in env]
    print(f"env_variables injected: {sorted(env)}")
    if missing:
        print(f"  WARNING: missing {missing} — datastore calls will 500")
    return json.dumps(cfg, indent=2)


n = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for f in ("index.py", "catalyst_adapter.py", "requirements.txt"):
        z.write(os.path.join(SRC, f), f)
        n += 1
    z.writestr("catalyst-config.json", build_config())
    n += 1
    # Credentials ride in the bundle: Catalyst has no env-var UI for functions
    # and its console upload ignores deployment.env_variables. index.py loads
    # this into os.environ before app.config is imported.
    if os.path.exists(".env"):
        z.write(".env", ".env")
        n += 1
        print("bundled .env (credentials are inside the zip — keep it private)")
    else:
        print("WARNING: no .env found — datastore calls will 500")
    n += add_tree(z, "app", "app/")
    n += add_tree(z, VENDOR, "vendor/")

names = zipfile.ZipFile(OUT).namelist()
print(f"wrote {OUT} ({n} files, {os.path.getsize(OUT) / 1024 / 1024:.1f} MB)")

# the top-level .env is deliberate; anything else of that shape is not
bad = [x for x in names
       if "__pycache__" in x or x.endswith(".pyc")
       or (x.endswith(".env") and x != ".env")]
print("unexpected cache/secret files:", bad or "none")

# the compiled extension is the thing most likely to be silently wrong
so = [x for x in names if x.endswith(".so")]
wrong = [x for x in so if "linux" not in x]
print(f"native ext: {len(so)} .so, non-linux: {wrong or 'none'}")
assert "index.py" in names, "entry point missing"
assert not wrong, "host-platform binaries leaked into bundle"
assert any("vendor/pydantic_core/" in x for x in names), "pydantic_core missing"
print("OK")
