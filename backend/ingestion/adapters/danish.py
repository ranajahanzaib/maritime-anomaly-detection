import datetime
from pathlib import Path
from typing import Iterator, Dict, Any, List
import polars as pl

from backend.ingestion.adapters.base import BaseAISAdapter
from backend.ingestion.normalization.schema import CanonicalAISPoint, normalize_vessel_type


class DanishAISAdapter(BaseAISAdapter):
    """
    Adapter for Danish Maritime Authority (DMA) AIS Trajectory Datasets
    and abnormal-behaviour benchmark datasets (KristofferOlesen/Datasets-of-AIS-Trajectories-from-Danish-Waters).
    """
    @property
    def source_name(self) -> str:
        return "DANISH_AIS"

    def inspect_schema(self, file_path: Path) -> Dict[str, Any]:
        path_str = str(file_path)
        if path_str.endswith(".parquet"):
            df = pl.read_parquet(path_str, n_rows=100)
        else:
            df = pl.read_csv(path_str, n_rows=100, separator=",", ignore_errors=True)

        return {
            "columns": df.columns,
            "sample_count": len(df),
            "source": self.source_name,
            "provenance": "Danish Maritime Authority / Datasets of AIS Trajectories from Danish Waters",
            "license": "Open Data / DMA terms of use",
        }

    def parse(self, file_path: Path, limit: int | None = None) -> Iterator[CanonicalAISPoint]:
        path_str = str(file_path)
        if path_str.endswith(".parquet"):
            lazy_df = pl.scan_parquet(path_str)
        else:
            lazy_df = pl.scan_csv(path_str, separator=",", ignore_errors=True)

        if limit:
            lazy_df = lazy_df.limit(limit)

        df = lazy_df.collect()
        col_map = {c.lower().replace("#", "").strip(): c for c in df.columns}

        def get_val(row_dict: dict, *keys, default=None):
            for k in keys:
                actual_k = col_map.get(k.lower().strip())
                if actual_k and row_dict.get(actual_k) is not None:
                    return row_dict[actual_k]
            return default

        for row in df.iter_rows(named=True):
            try:
                mmsi_raw = get_val(row, "mmsi")
                if mmsi_raw is None:
                    continue
                mmsi = int(float(mmsi_raw))

                time_raw = get_val(row, "timestamp", "date_time", "time")
                if isinstance(time_raw, str):
                    try:
                        # DMA often uses DD/MM/YYYY HH:MM:SS or ISO format
                        if "/" in time_raw:
                            ts = datetime.datetime.strptime(time_raw[:19], "%d/%m/%Y %H:%M:%S")
                        else:
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

                name = str(get_val(row, "name", "vessel_name", default="")).strip() or None
                vtype = normalize_vessel_type(get_val(row, "ship type", "shiptype", "type of mobile", "type"))
                status = str(get_val(row, "navigational status", "status", default="Under way using engine"))

                imo_raw = get_val(row, "imo")
                imo = int(float(imo_raw)) if imo_raw is not None and float(imo_raw) > 0 else None
                length = float(get_val(row, "length")) if get_val(row, "length") is not None else None
                width = float(get_val(row, "width")) if get_val(row, "width") is not None else None
                draught = float(get_val(row, "draught", "draft")) if get_val(row, "draught", "draft") is not None else None

                yield CanonicalAISPoint(
                    mmsi=mmsi,
                    imo=imo,
                    vessel_name=name,
                    vessel_type=vtype,
                    flag="DNK",
                    timestamp=ts,
                    latitude=lat,
                    longitude=lon,
                    sog=sog,
                    cog=cog,
                    heading=heading,
                    navigational_status=status,
                    length=length,
                    width=width,
                    draught=draught,
                    source_dataset="DANISH_AIS",
                    original_record_id=str(row.get("id", "")),
                )
            except Exception:
                continue

    @staticmethod
    def load_annotations(annotation_path: Path) -> List[Dict[str, Any]]:
        """
        Loads abnormal behaviour trajectory annotations from Danish waters dataset.
        """
        if not annotation_path.exists():
            return []
        
        df = pl.read_csv(str(annotation_path), ignore_errors=True)
        annotations = []
        for row in df.iter_rows(named=True):
            annotations.append({
                "mmsi": int(row.get("mmsi") or 0),
                "incident_category": str(row.get("anomaly_type") or row.get("label") or "ROUTE_DEVIATION"),
                "start_time": str(row.get("start_time")),
                "end_time": str(row.get("end_time")),
                "description": str(row.get("notes") or row.get("description") or ""),
                "dataset": "DANISH_AIS",
            })
        return annotations
