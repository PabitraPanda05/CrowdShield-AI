import uuid
from datetime import datetime, timezone

from backend.services.incident_service import incident_service


def main():
    print("\nInitializing alert database...")
    incident_service.initialize()

    test_id = f"TEST-CAM002-{uuid.uuid4().hex[:8]}"
    session_id = f"TEST-{uuid.uuid4().hex[:8]}"

    print("\nCreating controlled HIGH alert...")

    inserted = incident_service.record_alert(
        alert_id=test_id,
        camera_id="CAM-002",
        session_id=session_id,
        batch_number=1,
        window_id=1,
        risk_level="HIGH",
        risk_score=50.0,
        camera_name="Laptop Webcam",
        source_type="webcam",
        dominant_factor="crowd",
        response_action="HIGH-PRIORITY MONITORING",
        response_priority="HIGH",
        response_reason="Controlled HIGH risk test.",
        active_signals=["test_signal"],
        start_time=datetime.now(timezone.utc).isoformat(),
        end_time=datetime.now(timezone.utc).isoformat(),
    )

    print("Alert inserted:", inserted)

    alerts = incident_service.list_alerts(
        camera_id="CAM-002",
        risk_level="HIGH",
        limit=200,
    )

    matching = [
        alert for alert in alerts
        if alert.get("alert_id") == test_id
    ]

    assert matching, "Test alert was not found in SQLite."

    alert = matching[0]

    print("\nRetrieved alert:")
    print("Alert ID:", alert.get("alert_id"))
    print("Camera:", alert.get("camera_id"))
    print("Risk level:", alert.get("risk_level"))
    print("Risk score:", alert.get("risk_score"))
    print("Status:", alert.get("status"))

    assert alert.get("status") == "OPEN", (
        "Expected initial status OPEN."
    )

    history = incident_service.history(
        alert_id=test_id,
        limit=50,
    )

    print("\nIncident history:")

    for event in history:
        print(event)

    assert history, "No incident history was recorded."

    print("\nSUCCESS: HIGH alert persisted in SQLite.")
    print("SUCCESS: Initial incident status is OPEN.")
    print("SUCCESS: Incident history exists.")
    print("\nTest alert ID:", test_id)


if __name__ == "__main__":
    main()