"""
Tier classification and activity scoring for repos.

Tier 1 — high-activity; gets a full repo .md with runbook and dep analysis
Tier 2 — moderate; mentioned in domain .md only
Tier 3 — stale/archived; gets a one-line stub in archive/
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

NOW = datetime.now(timezone.utc)


@dataclass
class RepoMeta:
    name: str
    org: str
    pushed_at: datetime | None
    archived: bool
    open_prs: int
    open_issues: int
    commits_30d: int
    unique_authors_90d: int
    has_release_180d: bool
    stars: int
    # from previous scan; None if first scan
    previous_tier: int | None = None
    # from domains.yml
    in_allowlist: bool = False
    in_denylist: bool = False
    pin_tier: int | None = None


Tier = Literal[1, 2, 3]


def _days_since(dt: datetime | None) -> float:
    if dt is None:
        return float("inf")
    return (NOW - dt).total_seconds() / 86400


def _tier1_conditions(r: RepoMeta) -> list[str]:
    reasons: list[str] = []
    days = _days_since(r.pushed_at)
    if days <= 90 and (r.commits_30d >= 5 or r.unique_authors_90d >= 3):
        reasons.append("active-90d")
    if r.open_prs >= 3:
        reasons.append("open-prs")
    if r.in_allowlist:
        reasons.append("allowlisted")
    if r.has_release_180d and not r.archived:
        reasons.append("recent-release")
    return reasons


def _tier3_conditions(r: RepoMeta) -> list[str]:
    reasons: list[str] = []
    if r.archived:
        reasons.append("archived")
    if _days_since(r.pushed_at) > 365 and r.open_issues == 0 and r.open_prs == 0:
        reasons.append("dormant-365d")
    if r.in_denylist:
        reasons.append("denylisted")
    return reasons


def classify_tier(r: RepoMeta) -> tuple[Tier, str]:
    """Return (tier, reason_string)."""
    if r.pin_tier in (1, 2, 3):
        return r.pin_tier, "pinned"  # type: ignore[return-value]

    t3 = _tier3_conditions(r)
    if t3:
        return 3, ",".join(t3)

    t1 = _tier1_conditions(r)
    if t1:
        return 1, ",".join(t1)

    # Hysteresis: previous Tier-1 stays if meeting any threshold at 50%
    if r.previous_tier == 1:
        days = _days_since(r.pushed_at)
        half_ok = any([
            days <= 90 and (r.commits_30d >= 3 or r.unique_authors_90d >= 2),
            r.open_prs >= 2,
            r.has_release_180d,
        ])
        if half_ok:
            return 1, "hysteresis"

    return 2, "moderate"


def activity_score(r: RepoMeta) -> float:
    """Weighted normalized activity score in [0, 1]."""
    def log_norm(v: float, cap: float) -> float:
        return math.log1p(min(v, cap)) / math.log1p(cap)

    days = _days_since(r.pushed_at)
    recency = max(0.0, 1.0 - days / 365)
    score = (
        0.35 * log_norm(r.commits_30d, 100)
        + 0.25 * log_norm(r.unique_authors_90d, 20)
        + 0.20 * recency
        + 0.10 * log_norm(r.open_prs, 10)
        + 0.05 * log_norm(r.stars, 500)
        + 0.05 * (1.0 if r.has_release_180d else 0.0)
    )
    return round(score, 2)
