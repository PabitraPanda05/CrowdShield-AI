from pathlib import Path
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = (
    PROJECT_ROOT
    / "data"
    / "database"
    / "crowdshield.db"
)


class DatabaseService:

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH

    def connect(self):
        # Ensure the database directory exists without replacing the database.
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def health(self) -> Dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()

            integrity = row[0]

            tables = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
                """
            ).fetchall()

        return {
            "database": "sqlite",
            "path": str(self.db_path),
            "integrity": integrity,
            "tables": [
                row["name"]
                for row in tables
            ],
        }

    def get_cameras(self) -> List[Dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    camera_id,
                    camera_name,
                    source_file,
                    status,
                    source_type,
                    width,
                    height,
                    fps,
                    frame_count,
                    duration_sec,
                    live_stream,
                    created_at
                FROM cameras
                ORDER BY camera_id
                """
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def get_risk_windows(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:

        query = """
            SELECT *
            FROM risk_windows
            ORDER BY window_id
        """

        params = ()

        if limit is not None:
            query = """
                SELECT *
                FROM risk_windows
                ORDER BY window_id
                LIMIT ?
            """
            params = (max(0, int(limit)),)

        with self.connect() as connection:
            rows = connection.execute(
                query,
                params
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def get_latest_risk(self) -> Optional[Dict[str, Any]]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM risk_windows
                ORDER BY window_id DESC
                LIMIT 1
                """
            ).fetchone()

        return dict(row) if row else None

    def get_response_decisions(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:

        query = """
            SELECT *
            FROM response_decisions
            ORDER BY window_id
        """

        params = ()

        if limit is not None:
            query = """
                SELECT *
                FROM response_decisions
                ORDER BY window_id
                LIMIT ?
            """
            params = (max(0, int(limit)),)

        with self.connect() as connection:
            rows = connection.execute(
                query,
                params
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def get_latest_response(
        self
    ) -> Optional[Dict[str, Any]]:

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM response_decisions
                ORDER BY window_id DESC
                LIMIT 1
                """
            ).fetchone()

        return dict(row) if row else None

    def get_pipeline_runs(
        self
    ) -> List[Dict[str, Any]]:

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM pipeline_runs
                ORDER BY run_id DESC
                """
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def get_system_events(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:

        query = """
            SELECT *
            FROM system_events
            ORDER BY event_id DESC
        """

        params = ()

        if limit is not None:
            query = """
                SELECT *
                FROM system_events
                ORDER BY event_id DESC
                LIMIT ?
            """
            params = (max(0, int(limit)),)

        with self.connect() as connection:
            rows = connection.execute(
                query,
                params
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def get_summary(self) -> Dict[str, Any]:
        with self.connect() as connection:
            risk_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM risk_windows
                """
            ).fetchone()[0]

            response_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM response_decisions
                """
            ).fetchone()[0]

            camera_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM cameras
                """
            ).fetchone()[0]

            risk_stats = connection.execute(
                """
                SELECT
                    MIN(operational_risk_score),
                    AVG(operational_risk_score),
                    MAX(operational_risk_score)
                FROM risk_windows
                """
            ).fetchone()

            risk_distribution = connection.execute(
                """
                SELECT
                    operational_risk_level,
                    COUNT(*) AS count
                FROM risk_windows
                GROUP BY operational_risk_level
                """
            ).fetchall()

            response_distribution = connection.execute(
                """
                SELECT
                    response_action,
                    COUNT(*) AS count
                FROM response_decisions
                GROUP BY response_action
                """
            ).fetchall()

            latest_risk = connection.execute(
                """
                SELECT
                    window_id,
                    operational_risk_score,
                    operational_risk_level
                FROM risk_windows
                ORDER BY window_id DESC
                LIMIT 1
                """
            ).fetchone()

            latest_response = connection.execute(
                """
                SELECT
                    response_action,
                    response_priority,
                    human_review_required,
                    autonomous_emergency_action
                FROM response_decisions
                ORDER BY window_id DESC
                LIMIT 1
                """
            ).fetchone()

        return {
            "database": "sqlite",
            "risk_windows": risk_count,
            "response_decisions": response_count,
            "cameras": camera_count,
            "minimum_risk_score": risk_stats[0],
            "mean_risk_score": risk_stats[1],
            "maximum_risk_score": risk_stats[2],
            "risk_distribution": {
                row["operational_risk_level"]: row["count"]
                for row in risk_distribution
            },
            "response_distribution": {
                row["response_action"]: row["count"]
                for row in response_distribution
            },
            "latest_state": {
                "window_id": (
                    latest_risk["window_id"]
                    if latest_risk
                    else None
                ),
                "risk_score": (
                    latest_risk["operational_risk_score"]
                    if latest_risk
                    else None
                ),
                "risk_level": (
                    latest_risk["operational_risk_level"]
                    if latest_risk
                    else None
                ),
                "response_action": (
                    latest_response["response_action"]
                    if latest_response
                    else None
                ),
                "response_priority": (
                    latest_response["response_priority"]
                    if latest_response
                    else None
                ),
                "human_review_required": bool(
                    latest_response["human_review_required"]
                ) if latest_response else True,
                "autonomous_emergency_action": bool(
                    latest_response["autonomous_emergency_action"]
                ) if latest_response else False,
            },
            "human_review_required": True,
            "autonomous_emergency_action": False,
        }

    # ------------------------------------------------------------------
    # Historical crowd monitoring
    # ------------------------------------------------------------------

    def initialize_crowd_history(self) -> None:
        """
        Create the historical crowd snapshot table if it does not exist.

        This is an additive migration: existing tables and records are kept.
        """
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS crowd_history (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    camera_name TEXT,
                    captured_at TEXT NOT NULL,
                    person_count INTEGER NOT NULL DEFAULT 0,
                    risk_score REAL,
                    risk_level TEXT,
                    zone_occupancy_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_crowd_history_camera_time
                ON crowd_history (camera_id, captured_at)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_crowd_history_captured_at
                ON crowd_history (captured_at)
                """
            )

    def save_crowd_snapshot(
        self,
        camera_id: str,
        camera_name: Optional[str],
        person_count: int,
        risk_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        zone_occupancy: Optional[Dict[str, Any]] = None,
        captured_at: Optional[str] = None,
    ) -> int:
        """
        Save one crowd observation.

        zone_occupancy is expected to contain estimated counts in image-space
        grid cells (for example, a 4x4 grid); it is not people per square metre.
        """
        if not camera_id:
            raise ValueError("camera_id is required")

        timestamp = captured_at or datetime.now(timezone.utc).isoformat()
        occupancy_json = json.dumps(
            zone_occupancy or {},
            separators=(",", ":"),
        )

        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO crowd_history (
                    camera_id,
                    camera_name,
                    captured_at,
                    person_count,
                    risk_score,
                    risk_level,
                    zone_occupancy_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(camera_id),
                    camera_name,
                    timestamp,
                    max(0, int(person_count or 0)),
                    float(risk_score) if risk_score is not None else None,
                    risk_level,
                    occupancy_json,
                ),
            )

            return int(cursor.lastrowid)

    def get_crowd_snapshots(
        self,
        camera_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Return historical crowd snapshots in chronological order."""
        conditions = []
        params: List[Any] = []

        if camera_id:
            conditions.append("camera_id = ?")
            params.append(str(camera_id))

        if start_time:
            conditions.append("captured_at >= ?")
            params.append(start_time)

        if end_time:
            conditions.append("captured_at <= ?")
            params.append(end_time)

        where_clause = (
            "WHERE " + " AND ".join(conditions)
            if conditions
            else ""
        )

        safe_limit = max(1, min(int(limit), 100000))

        query = f"""
            SELECT
                snapshot_id,
                camera_id,
                camera_name,
                captured_at,
                person_count,
                risk_score,
                risk_level,
                zone_occupancy_json
            FROM crowd_history
            {where_clause}
            ORDER BY captured_at DESC, snapshot_id DESC
            LIMIT ?
        """
        params.append(safe_limit)

        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()

        snapshots = []
        for row in reversed(rows):
            item = dict(row)
            raw_occupancy = item.pop("zone_occupancy_json", "{}")

            try:
                item["zone_occupancy"] = json.loads(raw_occupancy or "{}")
            except (TypeError, json.JSONDecodeError):
                item["zone_occupancy"] = {}

            snapshots.append(item)

        return snapshots

    def get_crowd_history_summary(
        self,
        camera_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 20000,
    ) -> Dict[str, Any]:
        """
        Summarize recorded crowd history.

        The summary describes only snapshots actually stored after history
        collection was enabled; it does not reconstruct earlier crowd levels.
        """
        snapshots = self.get_crowd_snapshots(
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        if not snapshots:
            return {
                "history_available": False,
                "snapshot_count": 0,
                "camera_id": camera_id,
                "average_person_count": 0,
                "peak_person_count": 0,
                "peak_captured_at": None,
                "average_risk_score": None,
                "risk_distribution": {},
                "peak_periods": [],
                "hotspot_zones": [],
                "message": "No historical crowd snapshots are available for this filter.",
            }

        counts = [
            int(item.get("person_count") or 0)
            for item in snapshots
        ]

        peak_index = max(
            range(len(snapshots)),
            key=lambda index: counts[index],
        )
        peak_snapshot = snapshots[peak_index]

        risk_values = [
            float(item["risk_score"])
            for item in snapshots
            if item.get("risk_score") is not None
        ]

        risk_distribution: Dict[str, int] = {}
        hourly_counts: Dict[str, List[int]] = {}
        zone_totals: Dict[str, int] = {}

        for item in snapshots:
            level = item.get("risk_level") or "UNKNOWN"
            risk_distribution[level] = risk_distribution.get(level, 0) + 1

            timestamp = item.get("captured_at") or ""
            # ISO timestamps are grouped by their date and hour.
            hour_key = timestamp[:13] if len(timestamp) >= 13 else "unknown"
            hourly_counts.setdefault(hour_key, []).append(
                int(item.get("person_count") or 0)
            )

            occupancy = item.get("zone_occupancy") or {}
            if isinstance(occupancy, dict):
                for zone, value in occupancy.items():
                    try:
                        zone_count = int(value)
                    except (TypeError, ValueError):
                        continue
                    zone_totals[str(zone)] = (
                        zone_totals.get(str(zone), 0) + zone_count
                    )

        peak_periods = [
            {
                "period": period,
                "average_person_count": round(
                    sum(values) / len(values), 2
                ),
                "peak_person_count": max(values),
                "snapshot_count": len(values),
            }
            for period, values in hourly_counts.items()
        ]
        peak_periods.sort(
            key=lambda item: (
                item["peak_person_count"],
                item["average_person_count"],
            ),
            reverse=True,
        )

        hotspot_zones = [
            {
                "zone": zone,
                "total_occupancy": total,
            }
            for zone, total in zone_totals.items()
        ]
        hotspot_zones.sort(
            key=lambda item: item["total_occupancy"],
            reverse=True,
        )

        return {
            "history_available": True,
            "snapshot_count": len(snapshots),
            "camera_id": camera_id,
            "start_time": snapshots[0]["captured_at"],
            "end_time": snapshots[-1]["captured_at"],
            "average_person_count": round(
                sum(counts) / len(counts), 2
            ),
            "peak_person_count": max(counts),
            "peak_captured_at": peak_snapshot["captured_at"],
            "average_risk_score": (
                round(sum(risk_values) / len(risk_values), 2)
                if risk_values
                else None
            ),
            "risk_distribution": risk_distribution,
            "peak_periods": peak_periods[:10],
            "hotspot_zones": hotspot_zones[:16],
            "message": "Summary calculated from recorded crowd snapshots.",
        }


database_service = DatabaseService()