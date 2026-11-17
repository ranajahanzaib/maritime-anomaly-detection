import datetime
from pathlib import Path
from typing import Iterator, Dict, Any, List
import polars as pl

from backend.ingestion.adapters.base import BaseAISAdapter
from backend.ingestion.normalization.schema import CanonicalAISPoint, normalize_vessel_type


class HawaiiCoastGTAdapter(BaseAISAdapter):
    """
    Adapter for HawaiiCoast_GT dataset (Zenodo 8253611).
    Dataset provenance: Zenodo Record 8253611.
    Includes AIS trajectory data around Hawaiian archipelago with incident annotations.
    """
    @property
    def source_name(self) -> str:
        return "HAWAII_COAST_GT"

    def inspect_schema(self, file_path: Path) -> Dict[str, Any]:
        path_str = str(file_path)
        if path_str.endswith(".parquet"):
            df = pl.read_parquet(path_str, n_rows=100)
        else:
            df = pl.read_csv(path_str, n_rows=100, ignore_errors=True)

        return {
            "columns": df.columns,
            "sample_count": len(df),
            "source": self.source_name,
            "provenance": "Zenodo 8253611 (HawaiiCoast_GT Ground Truth Benchmark)",
            "license": "Creative Commons Attribution 4.0 International",
        }

    def parse(self, file_path: Path, limit: int | None = None) -> Iterator[CanonicalAISPoint]:
        path_str = str(file_path)
        if path_str.endswith(".parquet"):
            lazy_df = pl.scan_parquet(path_str)
        else:
            lazy_df = pl.scan_csv(path_str, ignore_errors=True)

        if limit:
            lazy_df = lazy_df.limit(limit)

        df = lazy_df.collect()
        col_map = {c.lower(): c for c in df.columns}

        def get_val(row_dict: dict, *keys, default=None):
            for k in keys:
                actual_k = col_map.get(k.lower())
                if actual_k and row_dict.get(actual_k) is not None:
                    return row_dict[actual_k]
            return default

        for row in df.iter_rows(named=True):
            try:
                mmsi_raw = get_val(row, "mmsi", "vessel_id", "vesselid")
                if mmsi_raw is None:
                    continue
                mmsi = int(float(mmsi_raw))

                time_raw = get_val(row, "timestamp", "datetime", "time", "date_time_utc")
                if isinstance(time_raw, str):
                    try:
                        ts = datetime.datetime.fromisoformat(time_raw.replace("Z", "+00:00"))
                    except Exception:
                        ts = datetime.datetime.strptime(time_raw[:19], "%Y-%m-%d %H:%M:%S")
                elif isinstance(time_raw, (datetime.datetime, datetime.date)):
                    ts = time_raw if isinstance(time_raw, datetime.datetime) else datetime.datetime.combine(time_raw, datetime.time.min)
                else:
                    continue

                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=datetime.timezone.utc)

                lat = float(get_val(row, "latitude", "lat", default=0.0))
                lon = float(get_val(row, "longitude", "lon", default=0.0))
                sog = float(get_val(row, "sog", "speed", default=0.0))
                cog = float(get_val(row, "cog", "course", default=0.0))
                heading_raw = get_val(row, "heading")
                heading = float(heading_raw) if heading_raw is not None and float(heading_raw) < 361.0 else None

                vtype = normalize_vessel_type(get_val(row, "vessel_type", "shiptype", "type"))
                name = str(get_val(row, "vessel_name", "shipname", default="")).strip() or None

                yield CanonicalAISPoint(
                    mmsi=mmsi,
                    imo=None,
                    vessel_name=name,
                    vessel_type=vtype,
                    flag="USA",
                    timestamp=ts,
                    latitude=lat,
                    longitude=lon,
                    sog=sog,
                    cog=cog,
                    heading=heading,
                    navigational_status=str(get_val(row, "status", default="Under way")),
                    source_dataset="HAWAII_COAST_GT",
                    original_record_id=str(get_val(row, "incident_id", default="")),
                )
            except Exception:
                continue

    @staticmethod
    def load_annotations(annotation_path: Path) -> List[Dict[str, Any]]:
        """
        Loads ground-truth incident annotations from HawaiiCoast_GT metadata.
        """
        if not annotation_path.exists():
            return []
        
        df = pl.read_csv(str(annotation_path), ignore_errors=True)
        annotations = []
        for row in df.iter_rows(named=True):
            annotations.append({
                "mmsi": int(row.get("mmsi") or row.get("vessel_id") or 0),
                "incident_category": str(row.get("incident_type") or row.get("category") or "ABNORMAL_TRAJECTORY"),
                "start_time": str(row.get("start_time")),
                "end_time": str(row.get("end_time")),
                "description": str(row.get("description") or ""),
                "dataset": "HAWAII_COAST_GT",
            })
        return annotations
