from src.crowd.crowd_intelligence import CrowdIntelligenceEngine

engine = CrowdIntelligenceEngine(1280, 720)

# Frame 1: Initial positions
tracks_1 = [
    {"track_id": 1, "center_x": 100, "center_y": 200},
    {"track_id": 2, "center_x": 150, "center_y": 200},
    {"track_id": 3, "center_x": 200, "center_y": 200},
    {"track_id": 4, "center_x": 300, "center_y": 200},
]

engine.movement_statistics(tracks_1, 1, 30)

# Frame 2: Three move EAST, one moves WEST
tracks_2 = [
    {"track_id": 1, "center_x": 150, "center_y": 200},
    {"track_id": 2, "center_x": 200, "center_y": 200},
    {"track_id": 3, "center_x": 250, "center_y": 200},
    {"track_id": 4, "center_x": 250, "center_y": 200},
]

movement = engine.movement_statistics(tracks_2, 2, 30)

result = engine.flow_analysis(movement["motion_vectors"])

print("\n========== REVERSE FLOW TEST ==========")

for key, value in result.items():
    print(f"{key}: {value}")