from __future__ import annotations

import re
from dataclasses import dataclass

_SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ASIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\/\+=]{12,}['\"]?"),
]

_IP_PRIVATE = re.compile(
    r"\b("
    r"10\.(?:\d{1,3}\.){2}\d{1,3}|"
    r"192\.168\.(?:\d{1,3}\.)\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[0-1])\.(?:\d{1,3}\.)\d{1,3}"
    r")\b"
)

@dataclass
class Redactor:
    enabled: bool = True

    def redact_text(self, text: str) -> str:
        if not self.enabled or not text:
            return text
        out = _IP_PRIVATE.sub("[REDACTED_IP]", text)
        for pat in _SECRET_PATTERNS:
            out = pat.sub("[REDACTED_SECRET]", out)
        return out
