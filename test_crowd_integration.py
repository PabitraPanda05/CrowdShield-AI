from src.crowd.crowd_intelligence import CrowdIntelligenceEngine

engine = CrowdIntelligenceEngine(1280, 720)

# Frame 1: Initial positions
tracks_1 = [
    {"track_id": 1, "center_x": 200, "center_y": 200},
    {"track_id": 2, "center_x": 210, "center_y": 210},
    {"track_id": 3, "center_x": 220, "center_y": 220},
    {"track_id": 4, "center_x": 230, "center_y": 230},
]

# Frame 2: Three move EAST, one moves WEST
tracks_2 = [
    {"track_id": 1, "center_x": 250, "center_y": 200},
    {"track_id": 2, "center_x": 260, "center_y": 210},
    {"track_id": 3, "center_x": 270, "center_y": 220},
    {"track_id": 4, "center_x": 180, "center_y": 230},
]

engine.analyze_frame(tracks_1, 1, 0.0, 30)

result = engine.analyze_frame(
    tracks_2, 2, 1 / 30, 30
)

print("\n========== COMPLETE CROWD INTELLIGENCE ==========")

keys = [
    "person_count",
    "moving_tracks",
    "mean_speed_px_per_sec",
    "dominant_flow_direction",
    "flow_coherence",
    "reverse_flow_count",
    "reverse_flow_ratio",
    "potential_bottleneck_count",
    "potential_bottleneck_zones",
]

for key in keys:
    print(f"{key}: {result[key]}")