import sqlite3
from pathlib import Path
from datetime import datetime

db = Path(r"C:\Users\pabit\CrowdShield-AI\data\database\crowdshield.db")
alert_id = "TEST-CAM002-8c042b65"

if not db.exists():
    raise SystemExit("Database not found.")

backup = db.with_name(
    f"crowdshield_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
)

conn = sqlite3.connect(db)

try:
    # Create backup before making changes.
    with sqlite3.connect(backup) as backup_conn:
        conn.backup(backup_conn)

    print("Backup created:", backup)

    conn.execute("BEGIN IMMEDIATE")

    row = conn.execute(
        """
        SELECT camera_id, session_id, response_reason
        FROM live_alerts
        WHERE alert_id = ?
        """,
        (alert_id,)
    ).fetchone()

    expected = (
        "CAM-002",
        "TEST-750912e9",
        "Controlled HIGH risk test."
    )

    if row != expected:
        raise RuntimeError(
            f"Verification failed. Found: {row}. Nothing deleted."
        )

    for table in (
        "incident_history",
        "alert_incidents",
        "live_alerts"
    ):
        columns = {
            item[1]
            for item in conn.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        }

        if "alert_id" not in columns:
            raise RuntimeError(
                f"Missing alert_id column in {table}"
            )

        cursor = conn.execute(
            f"DELETE FROM {table} WHERE alert_id = ?",
            (alert_id,)
        )

        print(table, "deleted:", cursor.rowcount)

    conn.commit()
    print("SUCCESS: Test alert removed.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()