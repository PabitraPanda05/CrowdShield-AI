from src.crowd.crowd_intelligence import CrowdIntelligenceEngine

engine = CrowdIntelligenceEngine(1280, 720)

# Frame 1: Three people in the same area
tracks_1 = [
    {"track_id": 1, "center_x": 200, "center_y": 200},
    {"track_id": 2, "center_x": 210, "center_y": 210},
    {"track_id": 3, "center_x": 220, "center_y": 220},
]

engine.movement_statistics(tracks_1, 1, 30)

# Frame 2: Very small movement
tracks_2 = [
    {"track_id": 1, "center_x": 200.2, "center_y": 200},
    {"track_id": 2, "center_x": 210.2, "center_y": 210},
    {"track_id": 3, "center_x": 220.2, "center_y": 220},
]

movement = engine.movement_statistics(tracks_2, 2, 30)

result = engine.bottleneck_analysis(
    tracks_2,
    movement["motion_vectors"]
)

print("\n========== BOTTLENECK TEST ==========")
print("Moving tracks:", movement["moving_tracks"])

for key, value in result.items():
    print(f"{key}: {value}")