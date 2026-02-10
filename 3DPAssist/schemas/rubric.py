from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import hashlib
import re


def _stable_id(seed: str) -> str:
    """
    Create a deterministic, short ID from text.
    This guarantees rubric and criterion IDs stay stable across runs.
    """
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return h[:12]


@dataclass(frozen=True)
class CriterionLevel:
    """
    Optional leveled rubric support.
    Example labels: Not Yet, Developing, Proficient, Advanced
    """
    label: str
    descriptor: str
    points: Optional[float] = None


@dataclass(frozen=True)
class RubricCriterion:
    """
    A single rubric criterion.
    This is the atomic unit of evaluation.
    """
    id: str
    category: str
    title: str
    descriptor: str
    max_points: Optional[float] = None
    levels: List[CriterionLevel] = field(default_factory=list)

    def validate(self) -> None:
        if not self.id or not re.match(r"^[a-zA-Z0-9_\-:.]{3,64}$", self.id):
            raise ValueError(f"Invalid criterion id: {self.id}")
        if not self.title.strip():
            raise ValueError(f"Criterion {self.id} has empty title.")
        if not self.descriptor.strip():
            raise ValueError(f"Criterion {self.id} has empty descriptor.")
        if self.max_points is not None and self.max_points <= 0:
            raise ValueError(f"Criterion {self.id} max_points must be > 0.")
        if self.levels:
            labels = [lvl.label.lower().strip() for lvl in self.levels]
            if len(labels) != len(set(labels)):
                raise ValueError(f"Duplicate level labels in criterion {self.id}.")


@dataclass(frozen=True)
class RubricCategory:
    """
    A grouping of related criteria (e.g., Process, Evidence, Reflection).
    """
    name: str
    criteria: List[RubricCriterion]

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("RubricCategory name cannot be empty.")
        if not self.criteria:
            raise ValueError(f"RubricCategory '{self.name}' has no criteria.")
        ids = [c.id for c in self.criteria]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate criterion IDs in category '{self.name}'.")
        for c in self.criteria:
            c.validate()


@dataclass(frozen=True)
class RubricVersion:
    """
    One specific version of a rubric.
    """
    rubric_id: str
    version: str
    title: str
    categories: List[RubricCategory]

    def validate(self) -> None:
        if not self.rubric_id.strip():
            raise ValueError("RubricVersion missing rubric_id.")
        if not self.version.strip():
            raise ValueError("RubricVersion missing version.")
        if not self.title.strip():
            raise ValueError("RubricVersion missing title.")
        if not self.categories:
            raise ValueError("RubricVersion must contain at least one category.")

        all_ids = []
        for cat in self.categories:
            cat.validate()
            all_ids.extend([c.id for c in cat.criteria])

        if len(all_ids) != len(set(all_ids)):
            raise ValueError("Duplicate criterion IDs across rubric categories.")

    def all_criteria(self) -> List[RubricCriterion]:
        criteria: List[RubricCriterion] = []
        for cat in self.categories:
            criteria.extend(cat.criteria)
        return criteria

    def fingerprint(self) -> str:
        """
        Stable hash of rubric content for audit and caching.
        """
        parts: List[str] = [self.rubric_id, self.version, self.title]
        for c in self.all_criteria():
            parts.extend([
                c.id,
                c.category,
                c.title,
                c.descriptor,
                str(c.max_points) if c.max_points is not None else "",
            ])
            for lvl in c.levels:
                parts.extend([
                    lvl.label,
                    lvl.descriptor,
                    str(lvl.points) if lvl.points is not None else "",
                ])
        blob = "\n".join(parts)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Rubric:
    """
    Container for all versions of a rubric.
    """
    rubric_id: str
    versions: List[RubricVersion]
    current_version: Optional[str] = None

    def validate(self) -> None:
        if not self.rubric_id.strip():
            raise ValueError("Rubric missing rubric_id.")
        if not self.versions:
            raise ValueError("Rubric must contain at least one version.")

        seen = set()
        for v in self.versions:
            v.validate()
            if v.version in seen:
                raise ValueError(f"Duplicate rubric version '{v.version}'.")
            seen.add(v.version)

    def get_version(self, version: Optional[str] = None) -> RubricVersion:
        target = version or self.current_version
        if not target:
            raise ValueError("No rubric version specified or set as current.")
        for v in self.versions:
            if v.version == target:
                return v
        raise ValueError(f"Rubric version '{target}' not found.")

    @staticmethod
    def create(title: str, categories: List[RubricCategory], version: str) -> Rubric:
        rubric_id = _stable_id(title.lower().strip())
        rv = RubricVersion(
            rubric_id=rubric_id,
            version=version,
            title=title,
            categories=categories,
        )
        return Rubric(
            rubric_id=rubric_id,
            versions=[rv],
            current_version=version,
        )
