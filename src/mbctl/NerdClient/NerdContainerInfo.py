from enum import Enum
from typing import List, Optional
import json
import re
from pydantic import BaseModel, Field, model_validator

class NerdContainerState(Enum):
    not_exist = "not_exist"
    running = "running"
    stopped = "stopped"
    unknown = "unknown"


class NerdContainerStatusKind(Enum):
    up = "up"
    created = "created"
    exited = "exited"
    other = "other"


class NerdContainerStatusInfo(BaseModel):
    kind: NerdContainerStatusKind
    raw: str
    since: Optional[str] = None
    exit_code: Optional[int] = None
    duration_seconds: Optional[int] = None


class NerdContainerInfo(BaseModel):
    command: str = Field(alias="Command")
    created_at: str = Field(alias="CreatedAt")
    id: str = Field(alias="ID")
    image: str = Field(alias="Image")
    platform: str = Field(alias="Platform")
    names: str = Field(alias="Names")
    ports: str = Field(alias="Ports")
    status: str = Field(alias="Status")
    runtime: str = Field(alias="Runtime")
    size: str = Field(alias="Size")
    labels: str = Field(alias="Labels")

    status_info: Optional[NerdContainerStatusInfo] = None

    @model_validator(mode="after")
    def _build_status_info(cls, values):
        status = values.get("status")
        if status and not values.get("status_info"):
            values["status_info"] = parse_status_info(status)
        return values

    class Config:
        validate_by_name = True


_DURATION_RE = re.compile(r"(?P<num>\d+)\s+(?P<unit>second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)")

_UNIT_SECONDS = {
    "second": 1, "seconds": 1,
    "minute": 60, "minutes": 60,
    "hour": 3600, "hours": 3600,
    "day": 86400, "days": 86400,
    "week": 604800, "weeks": 604800,
    "month": 2592000, "months": 2592000,
    "year": 31536000, "years": 31536000,
}


def _parse_duration_seconds(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = _DURATION_RE.search(text)
    if not m:
        return None
    num = int(m.group("num"))
    unit = m.group("unit")
    return num * _UNIT_SECONDS.get(unit, 0)


def parse_status_info(status: str) -> NerdContainerStatusInfo:
    s = status.strip()
    if s.startswith("Up"):
        since = s[len("Up"):].strip() or None
        return NerdContainerStatusInfo(
            kind=NerdContainerStatusKind.up,
            raw=s,
            since=since,
            duration_seconds=_parse_duration_seconds(since),
        )
    if s.startswith("Created"):
        since = s[len("Created"):].strip() or None
        return NerdContainerStatusInfo(
            kind=NerdContainerStatusKind.created,
            raw=s,
            since=since,
            duration_seconds=_parse_duration_seconds(since),
        )
    if s.startswith("Exited"):
        # Example: "Exited (0) 6 days ago"
        m = re.match(r"Exited\s+\((?P<code>\d+)\)\s*(?P<rest>.*)", s)
        exit_code = int(m.group("code")) if m else None
        since = m.group("rest").strip() if m else None
        return NerdContainerStatusInfo(
            kind=NerdContainerStatusKind.exited,
            raw=s,
            since=since or None,
            exit_code=exit_code,
            duration_seconds=_parse_duration_seconds(since),
        )
    return NerdContainerStatusInfo(
        kind=NerdContainerStatusKind.other,
        raw=s,
        since=s or None,
        duration_seconds=_parse_duration_seconds(s),
    )


def parse_nerdctl_ps_json_lines(output: str) -> List[NerdContainerInfo]:
    items: List[NerdContainerInfo] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(NerdContainerInfo.parse_obj(json.loads(line)))
    return items
