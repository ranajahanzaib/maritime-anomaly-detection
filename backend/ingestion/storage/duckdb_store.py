from pathlib import Path
from typing import List, Dict, Any, Optional
import duckdb
from backend.app.core.config import settings


class DuckDBStore:
    def __init__(self, storage_dir: Path | None = None):
        self.storage_dir = storage_dir or settings.STORAGE_DIR
        self.conn = duckdb.connect(":memory:")

    def get_parquet_path(self, dataset_id: Optional[str] = None) -> str:
        if dataset_id:
            p = self.storage_dir / dataset_id / "normalized_ais.parquet"
            if p.exists():
                return f"'{p.as_posix()}'"
        # Fallback to all parquet files in storage_dir
        return f"'{self.storage_dir.as_posix()}/*/*.parquet'"

    def query_points(
        self,
        dataset_id: Optional[str] = None,
        mmsi: Optional[int] = None,
        bbox: Optional[tuple[float, float, float, float]] = None,
        time_start: Optional[str] = None,
        time_end: Optional[str] = None,
        vessel_type: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        path_expr = self.get_parquet_path(dataset_id)
        
        where_clauses = ["is_valid = true"]
        if mmsi:
            where_clauses.append(f"mmsi = {mmsi}")
        if bbox:
            min_lat, min_lon, max_lat, max_lon = bbox
            where_clauses.append(
                f"latitude >= {min_lat} AND latitude <= {max_lat} AND longitude >= {min_lon} AND longitude <= {max_lon}"
            )
        if time_start:
            where_clauses.append(f"timestamp >= '{time_start}'")
        if time_end:
            where_clauses.append(f"timestamp <= '{time_end}'")
        if vessel_type and vessel_type != "All":
            where_clauses.append(f"vessel_type = '{vessel_type}'")

        where_stmt = " AND ".join(where_clauses)
        query = f"""
            SELECT mmsi, vessel_name, vessel_type, flag, timestamp, latitude, longitude, sog, cog, heading, navigational_status
            FROM read_parquet({path_expr})
            WHERE {where_stmt}
            ORDER BY timestamp ASC
            LIMIT {limit}
        """
        try:
            res = self.conn.execute(query).fetchall()
            cols = [
                "mmsi", "vessel_name", "vessel_type", "flag", "timestamp",
                "latitude", "longitude", "sog", "cog", "heading", "navigational_status"
            ]
            return [dict(zip(cols, row)) for row in res]
        except Exception:
            return []

    def compute_density_grid(
        self,
        dataset_id: Optional[str] = None,
        grid_size_deg: float = 0.05,
        bbox: Optional[tuple[float, float, float, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Aggregates vessel points into spatial grid cells for heatmap rendering.
        Returns cell center lat, lon, and point count / unique vessel count.
        """
        path_expr = self.get_parquet_path(dataset_id)
        where_clauses = ["is_valid = true"]
        if bbox:
            min_lat, min_lon, max_lat, max_lon = bbox
            where_clauses.append(
                f"latitude >= {min_lat} AND latitude <= {max_lat} AND longitude >= {min_lon} AND longitude <= {max_lon}"
            )
        where_stmt = " AND ".join(where_clauses)

        query = f"""
            SELECT 
                ROUND(latitude / {grid_size_deg}) * {grid_size_deg} AS cell_lat,
                ROUND(longitude / {grid_size_deg}) * {grid_size_deg} AS cell_lon,
                COUNT(*) AS count,
                COUNT(DISTINCT mmsi) AS unique_vessels,
                AVG(sog) AS avg_sog
            FROM read_parquet({path_expr})
            WHERE {where_stmt}
            GROUP BY cell_lat, cell_lon
            HAVING count > 0
            ORDER BY count DESC
            LIMIT 5000
        """
        try:
            res = self.conn.execute(query).fetchall()
            cols = ["lat", "lon", "count", "unique_vessels", "avg_sog"]
            return [dict(zip(cols, row)) for row in res]
        except Exception:
            return []
