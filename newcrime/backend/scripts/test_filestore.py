"""Evidence/witness/chat file round-trip through the File Store abstraction."""
import sys

sys.path.insert(0, ".")
from app.services import file_store  # noqa: E402
from app.config import settings  # noqa: E402

failed = 0


def check(label, cond, detail=""):
    global failed
    failed += not cond
    print(f"[{'ok' if cond else 'FAIL'}] {label}{('  ' + detail) if detail else ''}")


payload = b"CONFIDENTIAL: seized ledger page 3\x00\xff binary safe"
print(f"catalyst folders configured: evidence={bool(settings.evidence_folder_id)} "
      f"witness={bool(settings.witness_folder_id)} chat={bool(settings.chat_uploads_folder_id)}")

for kind, sub in (("evidence", "9001"), ("witness", "9001/witnesses"), ("chat", "global_chat")):
    up = file_store.upload_file(kind, "ledger.pdf", payload, sub)
    check(f"{kind}: upload returns id", bool(up["file_id"]),
          f"storage={up['storage']}")

    got = file_store.download_file(kind, up["file_id"], sub)
    check(f"{kind}: round-trips byte-identical", got == payload,
          "MISMATCH" if got != payload else f"{len(got or b'')}B")

    check(f"{kind}: delete succeeds", file_store.delete_file(kind, up["file_id"], sub))
    check(f"{kind}: gone after delete",
          file_store.download_file(kind, up["file_id"], sub) is None)

# a missing file must read as absent, not raise
check("missing file returns None",
      file_store.download_file("evidence", "does-not-exist", "9001") is None)
check("deleting a missing file is False",
      file_store.delete_file("evidence", "does-not-exist", "9001") is False)

print(f"\nfile_store.last_error: {file_store.last_error}")
print("ALL PASS" if not failed else f"{failed} FAILED")
sys.exit(1 if failed else 0)
