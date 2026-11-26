from src.risk.operational_risk import OperationalRiskEngine
from src.response.response_engine import ResponseDecisionEngine

risk_engine = OperationalRiskEngine()
response_engine = ResponseDecisionEngine()


def create_test_window(
    crowd,
    movement,
    movement_event,
    spatial,
    growth,
    persistence,
):
    return {
        "window_id": 1,
        "start_frame": 1,
        "end_frame": 25,
        "start_time": 0.0,
        "end_time": 1.0,
        "average_people": 20.0,
        "maximum_people": 30,
        "crowd_load": crowd,
        "movement_load": movement,
        "high_speed_signal": movement_event,
        "spatial_load": spatial,
        "growth_load": growth,
        "persistence": persistence,
    }


test_cases = {
    "HIGH": create_test_window(
        crowd=1.0,
        movement=1.0,
        movement_event=False,
        spatial=1.0,
        growth=0.0,
        persistence=0.0,
    ),

    "CRITICAL": create_test_window(
        crowd=1.0,
        movement=1.0,
        movement_event=True,
        spatial=1.0,
        growth=1.0,
        persistence=25.0,
    ),
}


for expected_level, window in test_cases.items():

    risk = risk_engine.calculate(window)

    response = response_engine.decide(risk)

    print("\n" + "=" * 50)
    print("EXPECTED:", expected_level)
    print("ACTUAL:", risk["operational_risk_level"])
    print("SCORE:", risk["operational_risk_score"])
    print("DOMINANT FACTOR:", risk["dominant_risk_factor"])
    print("RESPONSE:", response["response_action"])
    print("PRIORITY:", response["response_priority"])

    assert risk["operational_risk_level"] == expected_level

print("\nBoth risk classification tests passed.")