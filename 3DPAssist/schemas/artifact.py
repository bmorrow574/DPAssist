from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
import hashlib
import time


class ArtifactType(str, Enum):
    """
    Supported artifact types.
    """
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    LINK = "link"
    OTHER = "other"


@dataclass(frozen=True)
class Artifact:
    """
    Canonical representation of a single piece of student evidence.
    The orchestrator is responsible for extraction; schemas only store results.
    """
    artifact_id: str
    type: ArtifactType
    source_name: str  # filename, URL label, etc.

    text: str = ""
    captions: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    created_ts: float = field(default_factory=lambda: time.time())

    def validate(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("Artifact missing artifact_id.")
        if not self.source_name.strip():
            raise ValueError("Artifact missing source_name.")
        # text may be empty (e.g., image or link), but something must exist
        if not self.text.strip() and not self.captions and not self.meta:
            raise ValueError(
                f"Artifact '{self.artifact_id}' contains no usable evidence."
            )

    def fingerprint(self) -> str:
        """
        Stable hash of artifact contents for audit and caching.
        """
        blob = "\n".join([
            self.artifact_id,
            self.type.value,
            self.source_name,
            self.text,
            "\n".join(self.captions),
            str(sorted(self.meta.items(), key=lambda x: x[0])),
        ])
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ArtifactSet:
    """
    Group of artifacts submitted for a single evaluation run.
    """
    artifact_set_id: str
    artifacts: List[Artifact]
    created_ts: float = field(default_factory=lambda: time.time())

    def validate(self) -> None:
        if not self.artifact_set_id.strip():
            raise ValueError("ArtifactSet missing artifact_set_id.")
        if not self.artifacts:
            raise ValueError("ArtifactSet must contain at least one artifact.")

        ids = [a.artifact_id for a in self.artifacts]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate artifact_ids in ArtifactSet.")

        for a in self.artifacts:
            a.validate()

    def fingerprint(self) -> str:
        parts = [self.artifact_set_id] + [a.fingerprint() for a in self.artifacts]
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
