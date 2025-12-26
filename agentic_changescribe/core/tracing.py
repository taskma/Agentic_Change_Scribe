from __future__ import annotations

import json
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from agentic_changescribe.tools.redaction import Redactor

@dataclass
class TraceWriter:
    path: Path
    redactor: Redactor

    def write(self, event: Dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("ts", dt.datetime.utcnow().isoformat() + "Z")
        for k in ("prompt", "response"):
            if k in event and isinstance(event[k], str):
                event[k] = self.redactor.redact_text(event[k])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
