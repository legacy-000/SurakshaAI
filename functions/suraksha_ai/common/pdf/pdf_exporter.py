"""Upload generated PDF to Zoho Catalyst Stratus, with a local file fallback.

ponytail: local file fallback when Stratus SDK absent — local dev / no Catalyst.
"""
import os
import uuid
import tempfile
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_LOCAL_DIR = os.path.join(tempfile.gettempdir(), "suraksha_pdfs")
_DEFAULT_BUCKET = os.environ.get("SURAKSHA_STRATUS_BUCKET", "suraksha-reports")


def upload_to_stratus(pdf_bytes: bytes, filename: str) -> dict:
    """Upload PDF bytes. Returns {file_id, url, bucket, created_at}.

    Stratus SDK path uses zcatalyst_sdk; if unavailable, falls back to a local
    temp file so callers in local-dev still get a usable artifact.
    """
    created_at = datetime.now().isoformat()
    if not isinstance(pdf_bytes, (bytes, bytearray)):
        raise TypeError("pdf_bytes must be bytes")

    try:
        import zcatalyst_sdk  # type: ignore
        app = zcatalyst_sdk.initialize()
        store = app.stratus() if hasattr(app, "stratus") else app.store()
        key = f"reports/{filename}"
        # put_object may be a method name variant; tolerate both.
        if hasattr(store, "put_object"):
            store.put_object(_DEFAULT_BUCKET, key, bytes(pdf_bytes))
        elif hasattr(store, "upload_file"):
            store.upload_file(_DEFAULT_BUCKET, key, bytes(pdf_bytes))
        else:
            raise RuntimeError("Stratus store has no put_object/upload_file")
        return {
            "file_id": key,
            "url": f"stratus://{_DEFAULT_BUCKET}/{key}",
            "bucket": _DEFAULT_BUCKET,
            "created_at": created_at,
        }
    except Exception as e:
        logger.warning("Stratus upload failed (%s); using local fallback", e)
        os.makedirs(_LOCAL_DIR, exist_ok=True)
        local_path = os.path.join(_LOCAL_DIR, filename)
        with open(local_path, "wb") as f:
            f.write(pdf_bytes)
        return {
            "file_id": local_path,
            "url": None,
            "bucket": None,
            "created_at": created_at,
        }


def make_filename(investigation_id: str) -> str:
    # ponytail: keep the raw investigation_id prefix so the filename (and any
    # stratus key / fallback URL derived from it) is traceable and existing
    # contract tests that grep for the investigation_id can still resolve it.
    inv = (investigation_id or "report").replace("/", "_").replace(" ", "_")
    return f"report_{inv}_{uuid.uuid4().hex[:6]}.pdf"
