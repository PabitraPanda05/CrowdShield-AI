from pathlib import Path

DASHBOARD_FILE = Path(
    r"C:\Users\pabit\CrowdShield-AI\dashboard\crowdshield_dashboard.py"
)

content = DASHBOARD_FILE.read_text(
    encoding="utf-8"
)

pages = [
    "Risk Monitoring",
    "Crowd Intelligence",
    "Frame Monitor",
    "Alerts",
    "Camera",
    "Routing",
    "System",
]

changes = 0

for page in pages:

    old = f'elif page == "{page}":'

    new = (
        f'if page in ("{page}", "Command Center"):'
    )

    if old in content:

        content = content.replace(
            old,
            new,
            1
        )

        changes += 1

print("=" * 70)
print("CROWDSHIELD AI — FULL COMMAND CENTER PATCH")
print("=" * 70)

print("Dashboard:", DASHBOARD_FILE)
print("Sections changed:", changes)

if changes != len(pages):

    print()
    print("WARNING: Not all expected sections were found.")
    print("Expected:", len(pages))
    print("Found:", changes)
    print()
    print("No dashboard file will be saved.")

else:

    DASHBOARD_FILE.write_text(
        content,
        encoding="utf-8"
    )

    print()
    print("SUCCESS")
    print("Command Center will now display all dashboard sections.")
    print()
    print("Preserved:")
    print("- Individual sidebar pages")
    print("- Command Center")
    print("- Existing API logic")
    print("- Existing dashboard components")
    print()