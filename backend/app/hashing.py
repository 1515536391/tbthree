from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_bytes(obj: Any) -> bytes:
    """Canonical JSON bytes for hashing:

    - UTF-8
    - sort_keys=True
    - separators without spaces

    This must match the on-chain / script canonicalization rule.
    """
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return s.encode('utf-8')


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_hex_of_json(obj: Any) -> str:
    return sha256_hex(canonical_json_bytes(obj))
