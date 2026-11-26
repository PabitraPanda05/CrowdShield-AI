from src.crowd.crowd_intelligence import CrowdIntelligenceEngine

engine = CrowdIntelligenceEngine(1280, 720)

# Test 1: Establish initial positions
tracks_frame_1 = [
    {"track_id": 1, "center_x": 100, "center_y": 200},
    {"track_id": 2, "center_x": 150, "center_y": 200},
    {"track_id": 3, "center_x": 200, "center_y": 200},
]

engine.movement_statistics(tracks_frame_1, 1, 30)

# Test 2: Move all three tracks towards the right
tracks_frame_2 = [
    {"track_id": 1, "center_x": 150, "center_y": 200},
    {"track_id": 2, "center_x": 200, "center_y": 200},
    {"track_id": 3, "center_x": 250, "center_y": 200},
]

movement = engine.movement_statistics(tracks_frame_2, 2, 30)

print("\n========== MOVEMENT TEST ==========")
print("Moving tracks:", movement["moving_tracks"])

flow = engine.flow_analysis(movement["motion_vectors"])

print("\n========== FLOW ANALYSIS ==========")
for key, value in flow.items():
    print(f"{key}: {value}")

bottleneck = engine.bottleneck_analysis(
    tracks_frame_2,
    movement["motion_vectors"]
)

print("\n========== BOTTLENECK ANALYSIS ==========")
for key, value in bottleneck.items():
    print(f"{key}: {value}")