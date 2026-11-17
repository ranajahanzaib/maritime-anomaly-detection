import json
from pathlib import Path
from typing import Dict, Any, Optional
import torch
from backend.app.core.config import settings


class ModelArtifactStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or settings.MODELS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        model_id: str,
        model: torch.nn.Module,
        metadata: Dict[str, Any],
    ) -> str:
        model_dir = self.base_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        weights_path = model_dir / "weights.pt"
        meta_path = model_dir / "metadata.json"

        torch.save(model.state_dict(), weights_path)
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        return str(model_dir)

    def load_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        meta_path = self.base_dir / model_id / "metadata.json"
        if not meta_path.exists():
            return None
        with open(meta_path, "r") as f:
            return json.load(f)

    def load_weights(self, model_id: str, model: torch.nn.Module) -> bool:
        weights_path = self.base_dir / model_id / "weights.pt"
        if not weights_path.exists():
            return False
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        model.eval()
        return True
