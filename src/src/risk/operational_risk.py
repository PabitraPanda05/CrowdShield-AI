
from typing import Any, Dict

import numpy as np


class OperationalRiskEngine:
    """
    Explainable operational risk engine.

    Produces an analytical risk index from temporal
    crowd-intelligence features.

    IMPORTANT:
        The score is NOT a calibrated probability.
        It is NOT a prediction of injury or danger.
        It is an operational analytical index.
    """

    DEFAULT_WEIGHTS = {
        "crowd": 0.25,
        "movement": 0.15,
        "movement_event": 0.20,
        "spatial": 0.10,
        "growth": 0.15,
        "persistence": 0.15,
    }

    def __init__(
        self,
        weights: Dict[str, float] = None,
        moderate_threshold: float = 25.0,
        high_threshold: float = 50.0,
        critical_threshold: float = 70.0,
    ):
        self.weights = dict(
            weights
            if weights is not None
            else self.DEFAULT_WEIGHTS
        )

        required_weights = set(self.DEFAULT_WEIGHTS.keys())

        if set(self.weights.keys()) != required_weights:
            raise ValueError(
                "Weights must contain exactly: "
                f"{sorted(required_weights)}"
            )

        weight_sum = sum(self.weights.values())

        if not np.isclose(weight_sum, 1.0, atol=1e-6):
            raise ValueError(
                f"Risk weights must sum to 1.0. "
                f"Received {weight_sum:.6f}."
            )

        if not (
            0 <= moderate_threshold
            < high_threshold
            < critical_threshold
            <= 100
        ):
            raise ValueError(
                "Risk thresholds must satisfy "
                "0 <= moderate < high < critical <= 100."
            )

        self.moderate_threshold = float(moderate_threshold)
        self.high_threshold = float(high_threshold)
        self.critical_threshold = float(critical_threshold)

    # -----------------------------------------------------------------
    # Normalize persistence
    # -----------------------------------------------------------------

    @staticmethod
    def persistence_load(
        persistence: float,
        expected_frames: float = 25.0,
    ) -> float:
        """
        Convert temporal persistence to [0, 1].

        For a 25 FPS, 1-second window:
            25 observations = full persistence.

        This measures temporal coverage, not danger.
        """

        if expected_frames <= 0:
            raise ValueError(
                "expected_frames must be greater than zero."
            )

        return float(
            np.clip(
                float(persistence) / float(expected_frames),
                0.0,
                1.0,
            )
        )

    # -----------------------------------------------------------------
    # Risk level
    # -----------------------------------------------------------------

    def classify(self, risk_score: float) -> str:
        """Convert analytical risk score to an operational level."""

        score = float(np.clip(risk_score, 0.0, 100.0))

        if score < self.moderate_threshold:
            return "LOW"

        if score < self.high_threshold:
            return "MODERATE"

        if score < self.critical_threshold:
            return "HIGH"

        return "CRITICAL"

    # -----------------------------------------------------------------
    # Dominant factor
    # -----------------------------------------------------------------

    def dominant_factor(
        self,
        components: Dict[str, float],
    ) -> str:
        """Identify the largest weighted risk component."""

        if not components:
            return "NONE"

        return max(components, key=components.get)

    # -----------------------------------------------------------------
    # Human-readable explanation
    # -----------------------------------------------------------------

    def explain(
        self,
        window: Dict[str, Any],
        components: Dict[str, float],
        level: str,
    ) -> str:
        """Generate an explainable operational reason."""

        reasons = []

        if window["crowd_load"] >= 0.75:
            reasons.append("High crowd load")
        elif window["crowd_load"] >= 0.50:
            reasons.append("Elevated crowd load")

        if window["movement_load"] >= 0.50:
            reasons.append("Elevated movement")

        if bool(window["high_speed_signal"]):
            reasons.append("High-speed movement event")

        if window["spatial_load"] >= 0.75:
            reasons.append("High spatial concentration")

        # Crowd growth explanation requires multiple people.
        if (
            window["maximum_people"] > 1
            and window["growth_load"] >= 0.50
        ):
            reasons.append("Increasing crowd load")

        # Persistent crowd observation requires multiple
        # people in the observation window.
        if (
            window["maximum_people"] > 1
            and window["persistence"] >= 20
        ):
            reasons.append("Persistent crowd observation")

        if not reasons:
            reasons.append("No elevated operational signal")

        explanation = " + ".join(reasons)

        return f"{level}: {explanation}."

    # -----------------------------------------------------------------
    # Calculate risk
    # -----------------------------------------------------------------

    def calculate(
        self,
        window: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate the operational analytical risk index
        for one temporal window.
        """

        crowd = float(
            np.clip(window["crowd_load"], 0.0, 1.0)
        )

        movement = float(
            np.clip(window["movement_load"], 0.0, 1.0)
        )

        movement_event = float(
            1.0 if bool(window["high_speed_signal"]) else 0.0
        )

        spatial = float(
            np.clip(window["spatial_load"], 0.0, 1.0)
        )

        growth = float(
            np.clip(window["growth_load"], 0.0, 1.0)
        )

        persistence = self.persistence_load(
            window["persistence"]
        )

        # Weighted risk components
        components = {
            "crowd": crowd * self.weights["crowd"] * 100.0,
            "movement": (
                movement * self.weights["movement"] * 100.0
            ),
            "movement_event": (
                movement_event
                * self.weights["movement_event"]
                * 100.0
            ),
            "spatial": (
                spatial * self.weights["spatial"] * 100.0
            ),
            "growth": growth * self.weights["growth"] * 100.0,
            "persistence": (
                persistence
                * self.weights["persistence"]
                * 100.0
            ),
        }

        risk_score = float(
            np.clip(sum(components.values()), 0.0, 100.0)
        )

        level = self.classify(risk_score)
        dominant = self.dominant_factor(components)

        explanation = self.explain(
            window=window,
            components=components,
            level=level,
        )

        return {
            "window_id": int(window["window_id"]),
            "start_frame": int(window["start_frame"]),
            "end_frame": int(window["end_frame"]),
            "start_time": float(window["start_time"]),
            "end_time": float(window["end_time"]),
            "average_people": float(window["average_people"]),
            "maximum_people": int(window["maximum_people"]),

            "crowd_load": crowd,
            "movement_load": movement,
            "movement_event_signal": movement_event,
            "spatial_load": spatial,
            "growth_load": growth,
            "persistence_load": persistence,

            "risk_crowd": components["crowd"],
            "risk_movement": components["movement"],
            "risk_movement_event": components["movement_event"],
            "risk_spatial": components["spatial"],
            "risk_growth": components["growth"],
            "risk_persistence": components["persistence"],

            "operational_risk_score": risk_score,
            "operational_risk_level": level,
            "dominant_risk_factor": dominant,
            "operational_risk_reason": explanation,
        }

    # -----------------------------------------------------------------
    # Batch calculation
    # -----------------------------------------------------------------

    def calculate_batch(self, windows):
        """Calculate operational risk for a collection of windows."""

        return [
            self.calculate(window)
            for window in windows
        ]
