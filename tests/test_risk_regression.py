
import unittest

import pandas as pd

from src.risk.risk_features import RiskFeatureEngine
from src.risk.temporal_aggregator import TemporalRiskAggregator
from src.risk.operational_risk import OperationalRiskEngine


class TestRiskRegression(unittest.TestCase):

    def setUp(self):
        self.features = RiskFeatureEngine()
        self.aggregator = TemporalRiskAggregator(fps=25)
        self.operational = OperationalRiskEngine()

    def make_frame(self, frame, people, speed=100.0):
        record = {
            "frame": frame,
            "time_seconds": frame / 25.0,
            "person_count": people,
            "mean_speed_px_per_sec": speed,
            "max_speed_px_per_sec": speed,
            "std_x": 0.3 if people > 1 else 0.0,
            "std_y": 0.3 if people > 1 else 0.0,
        }
        return self.features.extract(record)

    def test_single_person_has_no_spatial_risk(self):
        result = self.make_frame(1, people=1)

        self.assertEqual(result["spatial_load"], 0.0)

    def test_movement_event_threshold(self):
        below = self.features.movement_event(749.0)
        at_threshold = self.features.movement_event(750.0)

        self.assertFalse(below["movement_event"])
        self.assertTrue(at_threshold["movement_event"])

    def test_single_person_window_has_no_crowd_persistence(self):
        records = [
            self.make_frame(frame, people=1)
            for frame in range(25)
        ]

        window = self.aggregator.aggregate_window(
            pd.DataFrame(records),
            window_id=1,
        )

        self.assertEqual(window["spatial_load"], 0.0)
        self.assertEqual(window["persistence"], 0)
        self.assertFalse(window["high_speed_signal"])

    def test_sustained_crowd_is_counted(self):
        records = [
            self.make_frame(frame, people=5)
            for frame in range(25)
        ]

        window = self.aggregator.aggregate_window(
            pd.DataFrame(records),
            window_id=1,
        )

        self.assertEqual(window["maximum_people"], 5)
        self.assertEqual(window["persistence"], 25)
        self.assertGreater(window["spatial_load"], 0.0)

        result = self.operational.calculate(window)

        self.assertGreater(
            result["operational_risk_score"], 0.0
        )

    def test_movement_event_contributes_twenty_points(self):
        window = {
            "window_id": 1,
            "start_frame": 1,
            "end_frame": 25,
            "start_time": 0.0,
            "end_time": 1.0,
            "average_people": 1.0,
            "maximum_people": 1,
            "crowd_load": 0.2,
            "movement_load": 0.1,
            "spatial_load": 0.0,
            "growth_load": 0.0,
            "persistence": 0,
            "high_speed_signal": False,
        }

        without_event = self.operational.calculate(window)

        event_window = dict(window)
        event_window["high_speed_signal"] = True

        with_event = self.operational.calculate(event_window)

        difference = (
            with_event["operational_risk_score"]
            - without_event["operational_risk_score"]
        )

        self.assertAlmostEqual(difference, 20.0)


if __name__ == "__main__":
    unittest.main()
