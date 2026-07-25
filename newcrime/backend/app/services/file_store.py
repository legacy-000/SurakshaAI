"""Catalyst File Store wrapper for evidence, witness docs, and chat uploads.

Falls back to local disk when Catalyst is not configured. Serverless instances
have ephemeral disks, so the local path is a development convenience only —
anything written there is lost when the instance recycles.
"""
from __future__ import annotations

import io
import os
import uuid

from ..config import settings

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

# Last File Store failure, surfaced by /api/health. Evidence silently landing
# on an ephemeral disk instead of the File Store is a chain-of-custody problem.
last_error: str | None = None


def _folder(folder_type: str):
    """(folder handle, folder_id) for a logical folder, or (None, None)."""
    global last_error
    folder_id = {
        "evidence": settings.evidence_folder_id,
        "witness": settings.witness_folder_id,
        "chat": settings.chat_uploads_folder_id,
    }.get(folder_type)
    if not settings.use_catalyst:
        return None, None
    if not folder_id:
        last_error = f"{folder_type}: folder id not configured"
        return None, None
    try:
        from ..catalyst_ctx import init_sdk
        return init_sdk().filestore().folder(int(folder_id)), folder_id
    except Exception as e:
        last_error = f"{folder_type}: {type(e).__name__}: {e}"[:250]
        return None, None


def _local_path(file_id: str, subfolder: str) -> str:
    base = os.path.join(UPLOAD_ROOT, subfolder) if subfolder else UPLOAD_ROOT
    return os.path.join(base, file_id)


def upload_file(folder_type: str, filename: str, file_bytes: bytes,
                subfolder: str = "") -> dict:
    global last_error
    stored_name = f"{uuid.uuid4().hex}_{filename}"
    folder, _ = _folder(folder_type)

    if folder is not None:
        try:
            # the SDK validates isinstance(file, BufferedReader) — a bare
            # BytesIO is rejected
            result = folder.upload_file(stored_name,
                                        io.BufferedReader(io.BytesIO(file_bytes)))
            file_id = result.get("id") or result.get("file_id")
            if file_id:
                last_error = None
                return {"file_id": str(file_id), "stored_name": stored_name,
                        "storage": "catalyst"}
            last_error = f"{folder_type}: upload returned no id: {str(result)[:120]}"
        except Exception as e:
            last_error = f"{folder_type} upload: {type(e).__name__}: {e}"[:250]

    local_dir = os.path.join(UPLOAD_ROOT, subfolder) if subfolder else UPLOAD_ROOT
    os.makedirs(local_dir, exist_ok=True)
    with open(os.path.join(local_dir, stored_name), "wb") as fh:
        fh.write(file_bytes)
    return {"file_id": stored_name, "stored_name": stored_name, "storage": "local"}


def download_file(folder_type: str, file_id: str, subfolder: str = "") -> bytes | None:
    global last_error
    folder, _ = _folder(folder_type)
    if folder is not None and str(file_id).isdigit():
        try:
            return folder.download_file(int(file_id))
        except Exception as e:
            last_error = f"{folder_type} download: {type(e).__name__}: {e}"[:250]

    path = _local_path(str(file_id), subfolder)
    if os.path.exists(path):
        with open(path, "rb") as fh:
            return fh.read()
    return None


def delete_file(folder_type: str, file_id: str, subfolder: str = "") -> bool:
    global last_error
    folder, _ = _folder(folder_type)
    if folder is not None and str(file_id).isdigit():
        try:
            folder.delete_file(int(file_id))
            return True
        except Exception as e:
            last_error = f"{folder_type} delete: {type(e).__name__}: {e}"[:250]

    path = _local_path(str(file_id), subfolder)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
