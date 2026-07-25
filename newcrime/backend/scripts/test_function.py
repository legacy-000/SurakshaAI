"""Drive the Catalyst function handler with real Flask requests.

Builds the bundle layout the same way deploy does (index.py + app/ side by
side), then calls handler() exactly as Catalyst's python runtime would.
"""
import json
import os
import shutil
import sys
import tempfile

BACKEND = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
FN = os.path.join(BACKEND, "functions", "suraksha_api")

stage = tempfile.mkdtemp(prefix="catfn_")
for f in ("index.py", "catalyst_adapter.py", "requirements.txt", "catalyst-config.json"):
    shutil.copy(os.path.join(FN, f), stage)
shutil.copytree(os.path.join(BACKEND, "app"), os.path.join(stage, "app"),
                ignore=shutil.ignore_patterns("__pycache__"))
# credentials come from the console in the cloud; locally reuse the dev .env
if os.path.exists(os.path.join(BACKEND, ".env")):
    shutil.copy(os.path.join(BACKEND, ".env"), stage)

os.chdir(stage)
sys.path.insert(0, stage)

import index  # noqa: E402
from flask import Flask  # noqa: E402

assert index._init_error is None, (
    f"init failed at stage {index._init_stage}:\n{index._init_error}")
print(f"[ok] init reached stage: {index._init_stage}")

flask_app = Flask(__name__)


def call(method, path, body=None, headers=None):
    hdrs = {"X-User-Id": "1", "X-User-Name": "dgp", "X-User-Role": "dgp"}
    hdrs.update(headers or {})
    kw = {"method": method, "headers": hdrs}
    if body is not None:
        kw["json"] = body
    with flask_app.test_request_context(path, **kw):
        from flask import request
        return index.handler(request)


checks = [
    ("GET", "/api/health", None, 200),
    ("GET", "/server/suraksha_api/api/health", None, 200),  # prefix stripped
    ("POST", "/api/auth/login", {"username": "dgp", "password": "password"}, 200),
    ("GET", "/api/cases?limit=5", None, 200),
    ("GET", "/api/analytics/overview", None, 200),
]

failed = 0
for method, path, body, want in checks:
    resp = call(method, path, body)
    got = resp.status_code
    ok = got == want
    failed += not ok
    preview = resp.get_data(as_text=True)[:120].replace("\n", " ")
    print(f"[{'ok' if ok else 'FAIL'}] {method} {path} -> {got} (want {want}) {preview}")

# CORS preflight must survive the adapter too
resp = call("OPTIONS", "/api/cases", None,
            {"Origin": "http://localhost:5173",
             "Access-Control-Request-Method": "GET"})
cors_ok = "access-control-allow-origin" in {k.lower() for k in resp.headers.keys()}
failed += not cors_ok
print(f"[{'ok' if cors_ok else 'FAIL'}] OPTIONS preflight -> {resp.status_code} "
      f"cors_header={cors_ok}")


# A failing GLM must never hand its own prompt back as the "answer" — an
# officer would read "Question: ... Findings: ..." as generated analysis.
from app.llm.client import CatalystClient  # noqa: E402

glm = CatalystClient()
glm.available = True  # force the GLM path; zcatalyst_sdk import will fail
findings = "261 cases, 144 open."
narrated = glm.narrate("How many cases?", findings)
ok = narrated == findings
failed += not ok
print(f"\n[{'ok' if ok else 'FAIL'}] GLM failure -> narrate falls back to findings "
      f"(got {narrated[:60]!r})")

parsed = glm.generate_query("How many cases?", "schema")
ok = parsed["intent"] == "unknown" and not parsed["zcql"]
failed += not ok
print(f"[{'ok' if ok else 'FAIL'}] GLM failure -> generate_query intent=unknown, "
      f"no zcql ({parsed['reasoning'][:50]!r})")

ok = glm.last_error is not None
failed += not ok
print(f"[{'ok' if ok else 'FAIL'}] GLM failure recorded for /api/health: {glm.last_error!r}")

shutil.rmtree(stage, ignore_errors=True)
print("\n" + ("ALL PASS" if not failed else f"{failed} FAILED"))
sys.exit(1 if failed else 0)
