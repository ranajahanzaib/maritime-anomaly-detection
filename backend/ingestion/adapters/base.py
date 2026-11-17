from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Dict, Any, List
from backend.ingestion.normalization.schema import CanonicalAISPoint


class BaseAISAdapter(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the dataset source."""
        pass

    @abstractmethod
    def inspect_schema(self, file_path: Path) -> Dict[str, Any]:
        """Inspect file schema, row counts, and column names."""
        pass

    @abstractmethod
    def parse(self, file_path: Path, limit: int | None = None) -> Iterator[CanonicalAISPoint]:
        """Parse raw dataset into stream of CanonicalAISPoint objects."""
        pass

    def preview(self, file_path: Path, n: int = 10) -> List[Dict[str, Any]]:
        """Return preview of first n normalized points as dicts."""
        pts = []
        for i, pt in enumerate(self.parse(file_path, limit=n)):
            pts.append(pt.model_dump())
            if i + 1 >= n:
                break
        return pts
