from backend.services.incident_service import incident_service

# Use the HIGH alert created in the previous test
ALERT_ID = "TEST-CAM002-8c042b65"

def show_status(stage):
    alerts = incident_service.list_alerts(limit=200)

    alert = next(
        (item for item in alerts
         if item.get("alert_id") == ALERT_ID),
        None
    )

    assert alert is not None, "Alert not found!"

    print(f"\n{stage}")
    print("Alert ID:", ALERT_ID)
    print("Status:", alert.get("status"))

def main():
    print("Testing alert lifecycle...")

    # 1. Acknowledge
    incident_service.update(
        alert_id=ALERT_ID,
        action="acknowledge",
        actor="TEST_OPERATOR"
    )
    show_status("1. AFTER ACKNOWLEDGEMENT")

    # 2. Assign
    incident_service.update(
        alert_id=ALERT_ID,
        action="assign",
        actor="TEST_OPERATOR",
        officer="OFFICER-001",
        note="Assigned for testing"
    )
    show_status("2. AFTER ASSIGNMENT")

    # 3. Resolve
    incident_service.update(
        alert_id=ALERT_ID,
        action="resolve",
        actor="OFFICER-001",
        note="Controlled test resolved"
    )
    show_status("3. AFTER RESOLUTION")

    # 4. Reopen
    incident_service.update(
        alert_id=ALERT_ID,
        action="reopen",
        actor="TEST_OPERATOR",
        note="Testing reopen functionality"
    )
    show_status("4. AFTER REOPENING")

    # Verify history
    history = incident_service.history(
        alert_id=ALERT_ID,
        limit=50
    )

    print("\nINCIDENT HISTORY")
    for event in history:
        print(event.get("action"), "-", event.get("actor"))

    print("\nSUCCESS: Alert lifecycle test completed.")

if __name__ == "__main__":
    main()