from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional
import json
import re
from pydantic import BaseModel, Field, model_validator
from mbctl.MBLog import mb_logger


class NerdContainerState(Enum):
    not_exist = "not_exist"
    running = "running"
    stopped = "stopped"
    unknown = "unknown"


class NerdContainerStatusKind(Enum):
    up = "up"
    created = "created"
    exited = "exited"
    restarting = "restarting"
    other = "other"


SPECIAL_EXIT_CODES = {
    130: "INT",
    137: "KILL",
    143: "TERM",
    139: "SEGV",
}


_HUMAN_DURATION_RE = re.compile(
    r"^(?:About\s+)?(?:(?P<single>Less than a second)|(?P<num>\d+)\s+(?P<unit>second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)|an?\s+(?P<article_unit>minute|hour))(?:\s+ago)?$",
    re.IGNORECASE,
)


class NerdContainerStatusInfo(BaseModel):
    kind: NerdContainerStatusKind
    raw: str
    since: Optional[str] = None
    exit_code: Optional[int] = None
    duration_seconds: Optional[int] = None

    @staticmethod
    def _format_duration_short(duration_seconds: Optional[int]) -> str:
        if duration_seconds is None:
            return ""

        if duration_seconds >= 31536000:
            return f"{duration_seconds // 31536000}y"
        if duration_seconds >= 2592000:
            return f"{duration_seconds // 2592000}mo"
        if duration_seconds >= 604800:
            return f"{duration_seconds // 604800}w"
        if duration_seconds >= 86400:
            return f"{duration_seconds // 86400}d"
        if duration_seconds >= 3600:
            return f"{duration_seconds // 3600}h"
        if duration_seconds >= 60:
            return f"{duration_seconds // 60}m"
        return f"{duration_seconds}s"

    def __str__(self) -> str:
        # 统一输出短格式，避免状态信息过长
        short_duration = self._format_duration_short(self.duration_seconds)

        if self.kind == NerdContainerStatusKind.up:
            return f"Up,{short_duration}" if short_duration else "Up"
        elif self.kind == NerdContainerStatusKind.created:
            return f"Created,{short_duration}" if short_duration else "Created"
        elif self.kind == NerdContainerStatusKind.exited:
            parts = ["Exit"]
            if self.exit_code is not None:
                parts.append(
                    SPECIAL_EXIT_CODES.get(self.exit_code, str(self.exit_code))
                )
            if short_duration:
                parts.append(short_duration)
            return ",".join(parts)
        elif self.kind == NerdContainerStatusKind.restarting:
            parts = ["Restart"]
            if self.exit_code is not None:
                parts.append(
                    SPECIAL_EXIT_CODES.get(self.exit_code, str(self.exit_code))
                )
            if short_duration:
                parts.append(short_duration)
            return ",".join(parts)
        else:
            return self.raw


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

    @property
    def created_at_short(self) -> str:
        return _format_created_at_short(self.created_at)

    @model_validator(mode="after")
    def _build_status_info(self):
        if self.status and not self.status_info:
            self.status_info = parse_status_info(self.status)
        return self

    class Config:
        validate_by_name = True


_DURATION_RE = re.compile(
    r"(?P<num>\d+)\s+(?P<unit>second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)"
)

_UNIT_SECONDS = {
    "second": 1,
    "seconds": 1,
    "minute": 60,
    "minutes": 60,
    "hour": 3600,
    "hours": 3600,
    "day": 86400,
    "days": 86400,
    "week": 604800,
    "weeks": 604800,
    "month": 2592000,
    "months": 2592000,
    "year": 31536000,
    "years": 31536000,
}

# 逆向还原 https://github.com/docker/go-units/blob/main/duration.go
def _parse_duration_seconds(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = _DURATION_RE.search(text)
    if not m:
        return None
    num = int(m.group("num"))
    unit = m.group("unit")
    return num * _UNIT_SECONDS.get(unit, 0)


def _parse_human_duration_seconds(text: Optional[str]) -> Optional[int]:
    if not text:
        return None

    s = text.strip()
    m = _HUMAN_DURATION_RE.match(s)
    if not m:
        return _parse_duration_seconds(s)

    if m.group("single"):
        return 0

    if m.group("article_unit"):
        return _UNIT_SECONDS.get(m.group("article_unit").lower(), None)

    num = int(m.group("num"))
    unit = m.group("unit").lower()
    return num * _UNIT_SECONDS.get(unit, 0)


def _format_created_at_short(created_at: str, now: Optional[datetime] = None) -> str:
    if not created_at:
        return ""

    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return ""

    reference = now or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    duration_seconds = int((reference - dt).total_seconds())
    if duration_seconds < 0:
        duration_seconds = 0
    return NerdContainerStatusInfo._format_duration_short(duration_seconds)


def parse_status_info(status: str) -> NerdContainerStatusInfo:
    s = status.strip()
    if s.startswith("Up"):
        return NerdContainerStatusInfo(
            kind=NerdContainerStatusKind.up,
            raw=s,
        )
    elif s.startswith("Created"):
        return NerdContainerStatusInfo(
            kind=NerdContainerStatusKind.created,
            raw=s,
        )
    elif s.startswith("Exited"):
        # Example: "Exited (0) 6 days ago"
        m = re.match(r"Exited\s+\((?P<code>\d+)\)\s*(?P<rest>.*)", s)
        exit_code = int(m.group("code")) if m else None
        since = m.group("rest").strip() if m else None
        return NerdContainerStatusInfo(
            kind=NerdContainerStatusKind.exited,
            raw=s,
            since=since or None,
            exit_code=exit_code,
            duration_seconds=_parse_human_duration_seconds(since),
        )
    elif s.startswith("Restarting"):
        # Example: "Restarting (1) 5 seconds ago"
        m = re.match(r"Restarting\s+\((?P<code>\d+)\)\s*(?P<rest>.*)", s)
        exit_code = int(m.group("code")) if m else None
        since = m.group("rest").strip() if m else None
        return NerdContainerStatusInfo(
            kind=NerdContainerStatusKind.restarting,
            raw=s,
            since=since or None,
            exit_code=exit_code,
        )
    else:
        mb_logger.warning(f"Unknown status kind: {s}")
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
        items.append(NerdContainerInfo.model_validate(json.loads(line)))
    return items
