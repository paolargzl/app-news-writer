from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict
import datetime as dt

@dataclass
class LocalTrace:
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def log(self, event_type: str, payload: Any) -> None:
        self.entries.append(
            {"ts": dt.datetime.now().isoformat(timespec="seconds"), "type": event_type, "payload": payload}
        )

    def to_markdown(self, max_entries: int = 200) -> str:
        shown = self.entries[-max_entries:]
        if not shown:
            return "_(sin eventos aún)_"
        return "\n".join([f"- `{e['ts']}` **{e['type']}**: {e['payload']}" for e in shown])
