"""
DTO for the `ctx.job.metadata` JSON blob sent by the dispatcher.
Only the fields we actually use today are modelled.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
import json


@dataclass
class CallMetadata:
    """Parsed metadata attached to the LiveKit job."""

    agent_id: str
    call_id: str

    # optional fields we already reference somewhere in `entrypoint.py`
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    phone_number: Optional[str] = None
    agent_data: Optional[Dict[str, Any]] = field(default_factory=dict)

    # keep a copy of the original blob in case we need something later
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    # -------- convenience helpers ---------------------------------
    @classmethod
    def from_json(cls, json_str: str | None) -> "CallMetadata":
        data: Dict[str, Any] = json.loads(json_str) if json_str else {}
        return cls(
            agent_id=data.get("agent_id", "default"),
            call_id=data.get("call_id", "unknown_call"),
            customer_name=data.get("customer_name"),
            customer_id=data.get("customer_id"),
            phone_number=data.get("phone_number"),
            agent_data=data.get("agent_data"),
            raw=data,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
