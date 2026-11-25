"""Private evidence storage.

Files are stored outside any served directory under a content-derived path.
User-supplied filenames never reach the filesystem, so a crafted upload cannot
traverse directories or overwrite another case's evidence.
"""

import hashlib
import secrets
from collections.abc import Iterator
from pathlib import Path

from app.core.config import settings

CHUNK_SIZE = 1024 * 1024


class StorageError(Exception):
    pass


def storage_root() -> Path:
    root = Path(settings.storage_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _relative_path(case_id, digest: str, suffix: str) -> Path:
    return Path("cases") / str(case_id) / digest[:2] / f"{digest}{suffix}"


def save_stream(case_id, source, *, max_bytes: int) -> tuple[str, str, int]:
    """Persist a binary stream, returning ``(relative_path, sha256, size)``.

    The file is written to a temporary name first and only renamed once the
    complete stream has been read and hashed.
    """
    root = storage_root()
    suffix = secrets.token_hex(4)
    tmp_path = root / f".upload-{suffix}.part"
    digest = hashlib.sha256()
    size = 0

    try:
        with tmp_path.open("wb") as target:
            while True:
                chunk = source.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise StorageError(
                        f"File exceeds the maximum upload size of {max_bytes} bytes."
                    )
                digest.update(chunk)
                target.write(chunk)
        if size == 0:
            raise StorageError("The uploaded file is empty.")

        sha256 = digest.hexdigest()
        relative = _relative_path(case_id, sha256, f"-{suffix}")
        final_path = root / relative
        final_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.replace(final_path)
        return str(relative).replace("\\", "/"), sha256, size
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def absolute_path(relative: str) -> Path:
    root = storage_root()
    candidate = (root / relative).resolve()
    if root not in candidate.parents and candidate != root:
        raise StorageError("Resolved evidence path escaped the storage root.")
    return candidate


def open_stream(relative: str) -> Iterator[bytes]:
    path = absolute_path(relative)
    if not path.exists():
        raise StorageError("Evidence file is missing from storage.")
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            yield chunk
