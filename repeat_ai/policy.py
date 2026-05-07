from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import List, Literal, Tuple

Verdict = Literal["DENY", "WARN", "ALLOW", "UNMATCHED"]

@dataclass(frozen=True)
class Policy:
    version: str
    deny: List[str]
    warn: List[str]
    allow: List[str]
    unmatched: Literal["warn", "deny", "allow"] = "warn"

    @staticmethod
    def load(path: Path) -> "Policy":
        d = json.loads(path.read_text(encoding="utf-8"))
        unmatched = str(d.get("unmatched", "warn")).lower()
        if unmatched not in ("warn", "deny", "allow"):
            unmatched = "warn"
        return Policy(
            version=str(d.get("version", "repeat-ai-policy-v1")),
            deny=list(d.get("deny", [])),
            warn=list(d.get("warn", [])),
            allow=list(d.get("allow", [])),
            unmatched=unmatched,  # type: ignore[arg-type]
        )

    def classify_path(self, path: str) -> Verdict:
        for pat in self.deny:
            if fnmatchcase(path, pat):
                return "DENY"
        for pat in self.allow:
            if fnmatchcase(path, pat):
                return "ALLOW"
        for pat in self.warn:
            if fnmatchcase(path, pat):
                return "WARN"
        return "UNMATCHED"

    def classify(self, path: str) -> Verdict:
        v = self.classify_path(path)
        if v != "UNMATCHED":
            return v
        if self.unmatched == "deny":
            return "DENY"
        if self.unmatched == "allow":
            return "ALLOW"
        return "WARN"

@dataclass(frozen=True)
class PolicyCounts:
    allow: int
    warn: int
    deny: int

    @property
    def total(self) -> int:
        return self.allow + self.warn + self.deny

@dataclass(frozen=True)
class PolicyResult:
    counts: PolicyCounts
    items: List[Tuple[str, Verdict]]

def evaluate_paths(paths: List[str], policy: Policy) -> PolicyResult:
    allow = warn = deny = 0
    items: List[Tuple[str, Verdict]] = []
    for p in paths:
        v = policy.classify(p)
        items.append((p, v))
        if v == "ALLOW":
            allow += 1
        elif v == "WARN":
            warn += 1
        else:
            deny += 1
    return PolicyResult(counts=PolicyCounts(allow=allow, warn=warn, deny=deny), items=items)
