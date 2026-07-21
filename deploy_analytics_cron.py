"""Deploy analytics_cron function to Catalyst via REST API.
Bypasses the CLI EMFILE bug by sending the pre-built zip directly.
"""
import json
import os
import sys
import subprocess

PROJECT_ID = "ksp-suraksha-ai"
ZIP_PATH = os.path.join(os.path.dirname(__file__), "analytics_cron_deploy.zip")
API_URL = f"https://api.catalyst.zoho.com/baas/v1/project/{PROJECT_ID}/function/upsert"

def get_token():
    result = subprocess.run(
        ["catalyst", "token:generate", "--current"],
        capture_output=True, text=True, cwd=os.path.dirname(__file__)
    )
    for line in result.stdout.splitlines():
        if "Token generated successfully" in line:
            return line.split(":")[-1].strip()
    raise RuntimeError("Could not get token from CLI")

def deploy(token):
    boundary = "----CatalystFormBoundary"
    filename = os.path.basename(ZIP_PATH)
    with open(ZIP_PATH, "rb") as f:
        zip_data = f.read()

    parts = []
    for field, value in [
        ("stack", "python_3_11"),
        ("name", "analytics_cron"),
        ("type", "basicio"),
    ]:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{value}\r\n")

    parts.append(
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"code\"; filename=\"{filename}\"\r\n"
        f"Content-Type: application/zip\r\n\r\n"
    )
    body = "".join(parts).encode("utf-8") + zip_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    import urllib.request
    req = urllib.request.Request(
        API_URL, data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.catalyst.v2+json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-CATALYST-Environment": "development",
        },
        method="PUT",
    )
    resp = urllib.request.urlopen(req)
    return resp.status, resp.read().decode()

if __name__ == "__main__":
    print("Getting auth token...")
    token = get_token()
    print("Uploading function...")
    status, body = deploy(token)
    print(f"Status: {status}")
    data = json.loads(body)
    if data.get("data"):
        print(f"Deployed: {data['data']['function_name']} (ID: {data['data']['id']})")
    else:
        print(f"Response: {json.dumps(data, indent=2)}")
