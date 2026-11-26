"""Persistent alert and human-managed incident lifecycle for CrowdShield AI."""

from pathlib import Path
import sqlite3
import json

from datetime import datetime, timezone
from typing import Any, Dict, Optional, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "database" / "crowdshield.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class IncidentService:

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH

    def connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row

        return conn

    # --------------------------------------------------
    # DATABASE INITIALIZATION
    # --------------------------------------------------

    def initialize(self) -> None:

        with self.connect() as conn:

            # Existing incident lifecycle table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_incidents (
                    alert_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'OPEN'
                        CHECK(status IN (
                            'OPEN',
                            'ACKNOWLEDGED',
                            'RESOLVED'
                        )),
                    assigned_officer TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    resolved_at TEXT,
                    resolution_note TEXT
                )
            """)

            # Existing incident action history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incident_history (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT,
                    details TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # New persistent AI-generated alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS live_alerts (
                    alert_id TEXT PRIMARY KEY,

                    camera_id TEXT NOT NULL,
                    camera_name TEXT,
                    source_type TEXT,

                    session_id TEXT NOT NULL,
                    batch_number INTEGER NOT NULL,
                    window_id INTEGER NOT NULL,

                    risk_level TEXT NOT NULL,
                    risk_score REAL,

                    dominant_factor TEXT,

                    response_action TEXT,
                    response_priority TEXT,
                    response_reason TEXT,

                    active_signals TEXT,

                    start_time TEXT,
                    end_time TEXT,

                    created_at TEXT NOT NULL,

                    UNIQUE (
                        camera_id,
                        session_id,
                        batch_number,
                        window_id
                    )
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_live_alerts_camera
                ON live_alerts(camera_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_live_alerts_created
                ON live_alerts(created_at)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_live_alerts_level
                ON live_alerts(risk_level)
            """)

    # --------------------------------------------------
    # RECORD A NEW AI ALERT
    # --------------------------------------------------

    def record_alert(
        self,
        alert_id: str,
        camera_id: str,
        session_id: str,
        batch_number: int,
        window_id: int,
        risk_level: str,
        risk_score: Optional[float] = None,
        camera_name: Optional[str] = None,
        source_type: Optional[str] = None,
        dominant_factor: Optional[str] = None,
        response_action: Optional[str] = None,
        response_priority: Optional[str] = None,
        response_reason: Optional[str] = None,
        active_signals: Optional[Any] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> bool:

        self.initialize()

        level = str(risk_level).upper()

        if level not in {"HIGH", "CRITICAL"}:
            return False

        if not alert_id or not camera_id or not session_id:
            raise ValueError(
                "alert_id, camera_id and session_id are required"
            )

        if active_signals is None:
            signals_json = None
        elif isinstance(active_signals, str):
            signals_json = active_signals
        else:
            signals_json = json.dumps(active_signals, default=str)

        now = _now()

        with self.connect() as conn:

            cursor = conn.execute("""
                INSERT OR IGNORE INTO live_alerts (
                    alert_id,
                    camera_id,
                    camera_name,
                    source_type,
                    session_id,
                    batch_number,
                    window_id,
                    risk_level,
                    risk_score,
                    dominant_factor,
                    response_action,
                    response_priority,
                    response_reason,
                    active_signals,
                    start_time,
                    end_time,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_id,
                camera_id,
                camera_name,
                source_type,
                session_id,
                batch_number,
                window_id,
                level,
                risk_score,
                dominant_factor,
                response_action,
                response_priority,
                response_reason,
                signals_json,
                start_time,
                end_time,
                now
            ))

            # Duplicate windows are ignored.
            if cursor.rowcount == 0:
                return False

            # Create incident automatically when alert is generated.
            conn.execute("""
                INSERT OR IGNORE INTO alert_incidents (
                    alert_id,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, 'OPEN', ?, ?)
            """, (alert_id, now, now))

            # Record alert generation in incident history.
            conn.execute("""
                INSERT INTO incident_history (
                    alert_id,
                    action,
                    actor,
                    details,
                    created_at
                )
                VALUES (?, 'GENERATED', 'AI_SYSTEM', ?, ?)
            """, (
                alert_id,
                f"{level} alert generated for {camera_id}",
                now
            ))

        return True

    # --------------------------------------------------
    # GET ALERTS WITH INCIDENT STATUS
    # --------------------------------------------------

    def list_alerts(
        self,
        camera_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:

        self.initialize()

        limit = max(1, min(int(limit), 1000))

        query = """
            SELECT
                a.*,
                COALESCE(i.status, 'OPEN') AS status,
                i.assigned_officer,
                i.acknowledged_at,
                i.resolved_at,
                i.resolution_note,
                i.updated_at AS incident_updated_at

            FROM live_alerts a

            LEFT JOIN alert_incidents i
                ON a.alert_id = i.alert_id

            WHERE 1=1
        """

        params = []

        if camera_id:
            query += " AND a.camera_id = ?"
            params.append(camera_id)

        if risk_level:
            query += " AND a.risk_level = ?"
            params.append(risk_level.upper())

        if status:
            query += " AND COALESCE(i.status, 'OPEN') = ?"
            params.append(status.upper())

        query += " ORDER BY a.created_at DESC LIMIT ?"
        params.append(limit)

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        results = []

        for row in rows:
            item = dict(row)

            try:
                item["active_signals"] = (
                    json.loads(item["active_signals"])
                    if item["active_signals"]
                    else []
                )
            except (json.JSONDecodeError, TypeError):
                item["active_signals"] = []

            results.append(item)

        return results

    # --------------------------------------------------
    # GET ONE INCIDENT
    # --------------------------------------------------

    def get(self, alert_id: str) -> Dict[str, Any]:

        self.initialize()

        with self.connect() as conn:
            row = conn.execute("""
                SELECT * FROM alert_incidents
                WHERE alert_id = ?
            """, (alert_id,)).fetchone()

        if row:
            return dict(row)

        return {
            "alert_id": alert_id,
            "status": "OPEN",
            "assigned_officer": None,
            "created_at": None,
            "updated_at": None,
            "acknowledged_at": None,
            "resolved_at": None,
            "resolution_note": None
        }

    # --------------------------------------------------
    # INCIDENT LIFECYCLE MANAGEMENT
    # --------------------------------------------------

    def update(
        self,
        alert_id: str,
        action: str,
        actor: str = "operator",
        officer: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:

        self.initialize()

        allowed = {
            "acknowledge",
            "assign",
            "resolve",
            "reopen"
        }

        if action not in allowed:
            raise ValueError("Unsupported incident action")

        now = _now()

        with self.connect() as conn:

            # Only allow lifecycle actions for an existing alert.
            alert = conn.execute("""
                SELECT alert_id FROM live_alerts
                WHERE alert_id = ?
            """, (alert_id,)).fetchone()

            if not alert:
                raise ValueError("Alert not found")

            conn.execute("""
                INSERT OR IGNORE INTO alert_incidents (
                    alert_id,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, 'OPEN', ?, ?)
            """, (alert_id, now, now))

            row = conn.execute("""
                SELECT * FROM alert_incidents
                WHERE alert_id = ?
            """, (alert_id,)).fetchone()

            current_status = row["status"]

            if action == "acknowledge":

                if current_status == "RESOLVED":
                    raise ValueError(
                        "Reopen the incident before acknowledging it"
                    )

                conn.execute("""
                    UPDATE alert_incidents
                    SET
                        status = 'ACKNOWLEDGED',
                        acknowledged_at = COALESCE(
                            acknowledged_at, ?
                        ),
                        updated_at = ?
                    WHERE alert_id = ?
                """, (now, now, alert_id))

            elif action == "assign":

                if current_status == "RESOLVED":
                    raise ValueError(
                        "Reopen the incident before assigning an officer"
                    )

                if not officer or not officer.strip():
                    raise ValueError(
                        "Officer name is required for assignment"
                    )

                conn.execute("""
                    UPDATE alert_incidents
                    SET assigned_officer = ?,
                        updated_at = ?
                    WHERE alert_id = ?
                """, (officer.strip(), now, alert_id))

            elif action == "resolve":

                if current_status == "RESOLVED":
                    raise ValueError("Incident is already resolved")

                conn.execute("""
                    UPDATE alert_incidents
                    SET
                        status = 'RESOLVED',
                        resolved_at = ?,
                        resolution_note = ?,
                        updated_at = ?
                    WHERE alert_id = ?
                """, (
                    now,
                    (note or "").strip() or None,
                    now,
                    alert_id
                ))

            elif action == "reopen":

                if current_status != "RESOLVED":
                    raise ValueError(
                        "Only resolved incidents can be reopened"
                    )

                conn.execute("""
                    UPDATE alert_incidents
                    SET
                        status = 'OPEN',
                        resolved_at = NULL,
                        resolution_note = NULL,
                        acknowledged_at = NULL,
                        updated_at = ?
                    WHERE alert_id = ?
                """, (now, alert_id))

            details = (
                officer.strip()
                if action == "assign" and officer
                else (note or "").strip() or None
            )

            conn.execute("""
                INSERT INTO incident_history (
                    alert_id,
                    action,
                    actor,
                    details,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                alert_id,
                action.upper(),
                (actor or "operator")[:120],
                details,
                now
            ))

            updated = conn.execute("""
                SELECT * FROM alert_incidents
                WHERE alert_id = ?
            """, (alert_id,)).fetchone()

        return dict(updated)

    # --------------------------------------------------
    # INCIDENT HISTORY
    # --------------------------------------------------

    def history(
        self,
        alert_id: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:

        self.initialize()

        limit = max(1, min(int(limit), 1000))

        with self.connect() as conn:

            if alert_id:
                rows = conn.execute("""
                    SELECT * FROM incident_history
                    WHERE alert_id = ?
                    ORDER BY event_id DESC
                    LIMIT ?
                """, (alert_id, limit)).fetchall()

            else:
                rows = conn.execute("""
                    SELECT * FROM incident_history
                    ORDER BY event_id DESC
                    LIMIT ?
                """, (limit,)).fetchall()

        return [dict(row) for row in rows]


incident_service = IncidentService()