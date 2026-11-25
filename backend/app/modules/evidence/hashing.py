"""SHA-256 helpers.

A hash proves the stored bytes match what was recorded. It does not prove the
file came from the claimed source, and FINTRACE says so wherever it shows one.
"""

import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


class HashingError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
