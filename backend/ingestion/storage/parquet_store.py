from pathlib import Path
from typing import List, Dict, Any
import datetime
import polars as pl
from backend.app.core.config import settings
from backend.ingestion.normalization.schema import CanonicalAISPoint


class ParquetStore:
    def __init__(self, base_storage_dir: Path | None = None):
        self.base_dir = base_storage_dir or settings.STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_dataset_points(
        self, dataset_id: str, points: List[CanonicalAISPoint]
    ) -> Dict[str, Any]:
        """
        Saves a list of CanonicalAISPoint objects as a partitioned columnar Parquet file.
        Returns dataset storage summary.
        """
        if not points:
            return {
                "file_path": None,
                "row_count": 0,
                "vessel_count": 0,
                "bbox": None,
                "time_range": None,
            }

        records = [p.model_dump() for p in points]
        df = pl.DataFrame(records)

        # Ensure timestamp is datetime
        if df["timestamp"].dtype != pl.Datetime:
            df = df.with_columns(pl.col("timestamp").str.to_datetime())

        # Create target dataset directory
        target_dir = self.base_dir / dataset_id
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "normalized_ais.parquet"

        df.write_parquet(
            file_path,
            compression="zstd",
            use_pyarrow=True,
        )

        min_lat = float(df["latitude"].min())
        max_lat = float(df["latitude"].max())
        min_lon = float(df["longitude"].min())
        max_lon = float(df["longitude"].max())

        time_min = df["timestamp"].min()
        time_max = df["timestamp"].max()

        vessel_count = int(df["mmsi"].n_unique())
        valid_count = int(df.filter(pl.col("is_valid") == True).height)
        rejected_count = len(df) - valid_count

        return {
            "file_path": str(file_path),
            "row_count": len(df),
            "valid_count": valid_count,
            "rejected_count": rejected_count,
            "vessel_count": vessel_count,
            "bbox_min_lat": min_lat,
            "bbox_min_lon": min_lon,
            "bbox_max_lat": max_lat,
            "bbox_max_lon": max_lon,
            "time_range_start": time_min,
            "time_range_end": time_max,
        }

    def read_dataset_df(self, dataset_id: str) -> pl.DataFrame:
        file_path = self.base_dir / dataset_id / "normalized_ais.parquet"
        if not file_path.exists():
            return pl.DataFrame()
        return pl.read_parquet(file_path)
