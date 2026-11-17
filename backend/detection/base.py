from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseDetector(ABC):
    @property
    @abstractmethod
    def detector_id(self) -> str:
        pass

    @property
    @abstractmethod
    def detector_version(self) -> str:
        pass

    @abstractmethod
    def detect(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Executes detection algorithm.
        Returns list of BehavioralEvent dicts with full explainability fields.
        """
        pass
