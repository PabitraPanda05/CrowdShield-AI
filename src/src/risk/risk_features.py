
from typing import Any, Dict, Optional

import numpy as np


class RiskFeatureEngine:
    """
    Production risk-feature engine.

    Converts raw crowd-intelligence measurements into
    normalized, explainable features.

    This class does NOT produce a final operational risk score.
    Final risk scoring belongs to the operational risk engine.
    """

    def __init__(
        self,
        reference_crowd_count: float = 13.0,
        reference_speed_px_per_sec: float = 1000.0,
        reference_spatial_spread: float = 0.50,
        movement_event_speed_px_per_sec: float = 750.0,
        crowd_growth_reference_per_sec: float = 2.0,
    ):
        if reference_crowd_count <= 0:
            raise ValueError(
                "reference_crowd_count must be greater than zero."
            )

        if reference_speed_px_per_sec <= 0:
            raise ValueError(
                "reference_speed_px_per_sec must be greater than zero."
            )

        if reference_spatial_spread <= 0:
            raise ValueError(
                "reference_spatial_spread must be greater than zero."
            )

        if movement_event_speed_px_per_sec <= 0:
            raise ValueError(
                "movement_event_speed_px_per_sec must be greater than zero."
            )

        if crowd_growth_reference_per_sec <= 0:
            raise ValueError(
                "crowd_growth_reference_per_sec must be greater than zero."
            )

        self.reference_crowd_count = float(
            reference_crowd_count
        )

        self.reference_speed_px_per_sec = float(
            reference_speed_px_per_sec
        )

        self.reference_spatial_spread = float(
            reference_spatial_spread
        )

        self.movement_event_speed_px_per_sec = float(
            movement_event_speed_px_per_sec
        )

        self.crowd_growth_reference_per_sec = float(
            crowd_growth_reference_per_sec
        )

        self.previous_count: Optional[float] = None
        self.previous_time: Optional[float] = None

    # -----------------------------------------------------------------
    # Normalization
    # -----------------------------------------------------------------

    @staticmethod
    def normalize(
        value: float,
        reference: float,
    ) -> float:
        """
        Normalize a non-negative value to [0, 1].
        """

        if reference <= 0:
            raise ValueError(
                "reference must be greater than zero."
            )

        value = max(float(value), 0.0)

        return float(
            np.clip(
                value / reference,
                0.0,
                1.0,
            )
        )

    # -----------------------------------------------------------------
    # Crowd load
    # -----------------------------------------------------------------

    def crowd_load(
        self,
        person_count: float,
    ) -> float:
        """
        Normalize current crowd count.

        This is a relative crowd-load feature, NOT a
        probability of danger.
        """

        return self.normalize(
            person_count,
            self.reference_crowd_count,
        )

    # -----------------------------------------------------------------
    # Movement load
    # -----------------------------------------------------------------

    def movement_load(
        self,
        mean_speed_px_per_sec: float,
    ) -> float:
        """
        Normalize mean image-space movement.
        """

        return self.normalize(
            mean_speed_px_per_sec,
            self.reference_speed_px_per_sec,
        )

    # -----------------------------------------------------------------
    # Spatial load
    # -----------------------------------------------------------------

    def spatial_load(
        self,
        std_x: float,
        std_y: float,
    ) -> float:
        """
        Estimate spatial concentration.

        Smaller spatial spread means more concentration.

        The returned value is normalized to [0, 1].

        This is an analytical feature and is NOT a calibrated
        crowd-danger probability.
        """

        spread = float(
            np.sqrt(
                max(float(std_x), 0.0) ** 2
                + max(float(std_y), 0.0) ** 2
            )
        )

        concentration = (
            1.0
            - (
                spread
                / self.reference_spatial_spread
            )
        )

        return float(
            np.clip(
                concentration,
                0.0,
                1.0,
            )
        )

    # -----------------------------------------------------------------
    # High-speed movement event
    # -----------------------------------------------------------------

    def movement_event(
        self,
        max_speed_px_per_sec: float,
    ) -> Dict[str, Any]:
        """
        Detect unusually high image-space movement.

        The threshold is an analytical engineering threshold,
        not a physical running-speed threshold.
        """

        speed = max(
            float(max_speed_px_per_sec),
            0.0,
        )

        triggered = (
            speed
            >= self.movement_event_speed_px_per_sec
        )

        intensity = self.normalize(
            speed,
            self.movement_event_speed_px_per_sec,
        )

        return {
            "movement_event": bool(triggered),
            "movement_event_intensity": intensity,
        }

    # -----------------------------------------------------------------
    # Crowd growth
    # -----------------------------------------------------------------

    def crowd_growth(
        self,
        person_count: float,
        timestamp_seconds: float,
    ) -> Dict[str, float]:
        """
        Calculate crowd growth rate using the previous
        observed frame.

        Returns:
            crowd_change
            crowd_growth_per_sec
        """

        current_count = float(
            person_count
        )

        current_time = float(
            timestamp_seconds
        )

        if (
            self.previous_count is None
            or self.previous_time is None
        ):
            growth = 0.0
            change = 0.0

        else:
            delta_time = (
                current_time
                - self.previous_time
            )

            if delta_time <= 0:
                growth = 0.0
            else:
                growth = (
                    current_count
                    - self.previous_count
                ) / delta_time

            change = (
                current_count
                - self.previous_count
            )

        self.previous_count = current_count
        self.previous_time = current_time

        return {
            "crowd_change": float(change),
            "crowd_growth_per_sec": float(growth),
        }

    # -----------------------------------------------------------------
    # Growth load
    # -----------------------------------------------------------------

    def growth_load(
        self,
        crowd_growth_per_sec: float,
    ) -> float:
        """
        Normalize positive crowd growth.
        """

        positive_growth = max(
            float(crowd_growth_per_sec),
            0.0,
        )

        return self.normalize(
            positive_growth,
            self.crowd_growth_reference_per_sec,
        )

    # -----------------------------------------------------------------
    # Complete feature extraction
    # -----------------------------------------------------------------

    def extract(
        self,
        crowd_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert one Crowd Intelligence record into
        normalized risk features.

        Retains raw movement statistics so that
        temporal aggregation can calculate accurate
        movement summaries.
        """

        person_count = float(
            crowd_record["person_count"]
        )

        timestamp = float(
            crowd_record["time_seconds"]
        )

        mean_speed = float(
            crowd_record[
                "mean_speed_px_per_sec"
            ]
        )

        median_speed = float(
            crowd_record[
                "median_speed_px_per_sec"
            ]
        )

        max_speed = float(
            crowd_record[
                "max_speed_px_per_sec"
            ]
        )

        moving_tracks = int(
            crowd_record["moving_tracks"]
        )

        std_x = float(
            crowd_record["std_x"]
        )

        std_y = float(
            crowd_record["std_y"]
        )

        crowd = self.crowd_load(
            person_count
        )

        movement = self.movement_load(
            mean_speed
        )

        # Spatial concentration requires at least two people.
        spatial = (
            self.spatial_load(
                std_x,
                std_y,
            )
            if person_count > 1
            else 0.0
        )

        event = self.movement_event(
            max_speed
        )

        growth = self.crowd_growth(
            person_count,
            timestamp,
        )

        growth_feature = self.growth_load(
            growth["crowd_growth_per_sec"]
        )

        return {
            "frame": int(
                crowd_record["frame"]
            ),

            "time_seconds": timestamp,

            "person_count": int(
                person_count
            ),

            "crowd_load": crowd,

            "movement_load": movement,

            # Preserve raw movement measurements.
            "moving_tracks": moving_tracks,

            "mean_speed_px_per_sec": mean_speed,

            "median_speed_px_per_sec": median_speed,

            "max_speed_px_per_sec": max_speed,

            "spatial_load": spatial,

            "movement_event": event[
                "movement_event"
            ],

            "movement_event_intensity": event[
                "movement_event_intensity"
            ],

            "crowd_change": growth[
                "crowd_change"
            ],

            "crowd_growth_per_sec": growth[
                "crowd_growth_per_sec"
            ],

            "growth_load": growth_feature,
        }

    # -----------------------------------------------------------------
    # Batch extraction
    # -----------------------------------------------------------------

    def extract_batch(
        self,
        crowd_records,
    ):
        """
        Extract risk features from multiple
        Crowd Intelligence records.
        """

        # Reset temporal state for a new sequence.
        self.previous_count = None
        self.previous_time = None

        return [
            self.extract(record)
            for record in crowd_records
        ]
