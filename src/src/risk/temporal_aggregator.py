
from typing import Any, Dict, List

import numpy as np
import pandas as pd


class TemporalRiskAggregator:
    """
    Convert frame-level risk features into temporal windows.

    Default:
        1 second windows.

    The purpose is to reduce frame-to-frame noise before
    operational risk scoring.

    This class does NOT calculate the final risk score.
    """

    def __init__(
        self,
        fps: float,
        window_seconds: float = 1.0,
    ):
        if fps <= 0:
            raise ValueError(
                "fps must be greater than zero."
            )

        if window_seconds <= 0:
            raise ValueError(
                "window_seconds must be greater than zero."
            )

        self.fps = float(fps)
        self.window_seconds = float(window_seconds)

        self.frames_per_window = max(
            1,
            int(round(
                self.fps * self.window_seconds
            )),
        )

    # -----------------------------------------------------------------
    # Aggregate one temporal window
    # -----------------------------------------------------------------

    def aggregate_window(
        self,
        window_df: pd.DataFrame,
        window_id: int,
    ) -> Dict[str, Any]:
        """
        Aggregate frame-level risk features into one temporal window.
        """

        if window_df.empty:
            raise ValueError(
                "Cannot aggregate an empty window."
            )

        # -------------------------------------------------------------
        # Frame and time boundaries
        # -------------------------------------------------------------

        start_frame = int(
            window_df["frame"].min()
        )

        end_frame = int(
            window_df["frame"].max()
        )

        start_time = float(
            window_df["time_seconds"].min()
        )

        end_time = float(
            window_df["time_seconds"].max()
        )

        # Total frames observed in this window.
        # This is distinct from crowd persistence.
        frame_count = int(len(window_df))

        # -------------------------------------------------------------
        # Crowd statistics
        # -------------------------------------------------------------

        average_people = float(
            window_df["person_count"].mean()
        )

        maximum_people = int(
            window_df["person_count"].max()
        )

        minimum_people = int(
            window_df["person_count"].min()
        )

        # -------------------------------------------------------------
        # Normalized loads
        # -------------------------------------------------------------

        crowd_load = float(
            window_df["crowd_load"].mean()
        )

        movement_load = float(
            window_df["movement_load"].mean()
        )

        # Spatial concentration is meaningful for this project
        # only when at least two people are present.
        crowd_frames = window_df[
            window_df["person_count"] > 1
        ]

        if crowd_frames.empty:
            spatial_load = 0.0
        else:
            spatial_load = float(
                crowd_frames["spatial_load"].mean()
            )

        # -------------------------------------------------------------
        # Movement events
        # -------------------------------------------------------------

        movement_event_count = int(
            window_df["movement_event"].sum()
        )

        movement_event_ratio = float(
            window_df["movement_event"].mean()
        )

        high_speed_signal = bool(
            movement_event_count > 0
        )

        maximum_event_intensity = float(
            window_df[
                "movement_event_intensity"
            ].max()
        )

        # -------------------------------------------------------------
        # Movement statistics
        # -------------------------------------------------------------

        mean_speed = float(
            window_df[
                "mean_speed_px_per_sec"
            ].mean()
            if "mean_speed_px_per_sec"
            in window_df.columns
            else 0.0
        )

        maximum_speed = float(
            window_df[
                "max_speed_px_per_sec"
            ].max()
            if "max_speed_px_per_sec"
            in window_df.columns
            else 0.0
        )

        # -------------------------------------------------------------
        # Temporal crowd growth
        # -------------------------------------------------------------

        # Calculate growth using the first and last observations
        # in the temporal window.

        first_count = float(
            window_df.iloc[0]["person_count"]
        )

        last_count = float(
            window_df.iloc[-1]["person_count"]
        )

        duration = max(
            end_time - start_time,
            1.0 / self.fps,
        )

        crowd_change = (
            last_count - first_count
        )

        crowd_growth_per_sec = (
            crowd_change / duration
        )

        # Positive growth only for the operational growth feature.

        positive_growth = max(
            crowd_growth_per_sec,
            0.0,
        )

        growth_load = float(
            np.clip(
                positive_growth / 2.0,
                0.0,
                1.0,
            )
        )

        # -------------------------------------------------------------
        # Crowd persistence
        # -------------------------------------------------------------

        # Count only frames containing at least two detected people.
        # Empty frames and single-person frames do not contribute
        # to crowd persistence.
        persistence = int(
            (window_df["person_count"] > 1).sum()
        )

        # -------------------------------------------------------------
        # Return temporal window
        # -------------------------------------------------------------

        return {
            "window_id": int(window_id),

            "start_frame": start_frame,
            "end_frame": end_frame,

            "start_time": start_time,
            "end_time": end_time,

            # Actual number of observations, regardless of crowd size.
            "frame_count": frame_count,

            "average_people": average_people,
            "maximum_people": maximum_people,
            "minimum_people": minimum_people,

            "crowd_load": crowd_load,
            "movement_load": movement_load,
            "spatial_load": spatial_load,

            "movement_event_count":
                movement_event_count,

            "movement_event_ratio":
                movement_event_ratio,

            "high_speed_signal":
                high_speed_signal,

            "maximum_event_intensity":
                maximum_event_intensity,

            "mean_speed_px_per_sec":
                mean_speed,

            "maximum_speed_px_per_sec":
                maximum_speed,

            "crowd_change":
                float(crowd_change),

            "crowd_growth_per_sec":
                float(crowd_growth_per_sec),

            "growth_load":
                growth_load,

            # Number of frames with at least two people.
            "persistence": persistence,
        }

    # -----------------------------------------------------------------
    # Aggregate complete sequence
    # -----------------------------------------------------------------

    def aggregate(
        self,
        frame_features: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Aggregate a complete frame-level risk-feature DataFrame.

        Expected columns include:
            frame
            time_seconds
            person_count
            crowd_load
            movement_load
            spatial_load
            movement_event
            movement_event_intensity
        """

        if frame_features.empty:
            raise ValueError(
                "frame_features cannot be empty."
            )

        required_columns = [
            "frame",
            "time_seconds",
            "person_count",
            "crowd_load",
            "movement_load",
            "spatial_load",
            "movement_event",
            "movement_event_intensity",
        ]

        missing = [
            column
            for column in required_columns
            if column not in frame_features.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}"
            )

        data = frame_features.copy()

        data = data.sort_values(
            "frame"
        ).reset_index(drop=True)

        results: List[Dict[str, Any]] = []

        window_id = 1

        for start in range(
            0,
            len(data),
            self.frames_per_window,
        ):
            end = min(
                start + self.frames_per_window,
                len(data),
            )

            window_df = data.iloc[start:end]

            result = self.aggregate_window(
                window_df=window_df,
                window_id=window_id,
            )

            results.append(result)

            window_id += 1

        return pd.DataFrame(results)

    # -----------------------------------------------------------------
    # Validation helper
    # -----------------------------------------------------------------

    def validate(
        self,
        aggregated: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Validate temporal aggregation output.
        """

        if aggregated.empty:
            return {
                "valid": False,
                "reason": "No aggregated windows.",
            }

        required_columns = [
            "window_id",
            "start_frame",
            "end_frame",
            "frame_count",
            "average_people",
            "maximum_people",
            "crowd_load",
            "movement_load",
            "spatial_load",
            "movement_event_count",
            "high_speed_signal",
            "crowd_growth_per_sec",
            "growth_load",
            "persistence",
        ]

        missing = [
            column
            for column in required_columns
            if column not in aggregated.columns
        ]

        if missing:
            return {
                "valid": False,
                "reason": f"Missing columns: {missing}",
            }

        if not aggregated["crowd_load"].between(
            0.0, 1.0
        ).all():
            return {
                "valid": False,
                "reason": "Invalid crowd_load.",
            }

        if not aggregated["movement_load"].between(
            0.0, 1.0
        ).all():
            return {
                "valid": False,
                "reason": "Invalid movement_load.",
            }

        if not aggregated["spatial_load"].between(
            0.0, 1.0
        ).all():
            return {
                "valid": False,
                "reason": "Invalid spatial_load.",
            }

        if not aggregated["growth_load"].between(
            0.0, 1.0
        ).all():
            return {
                "valid": False,
                "reason": "Invalid growth_load.",
            }

        if (
            (aggregated["frame_count"] < 0).any()
            or (aggregated["persistence"] < 0).any()
        ):
            return {
                "valid": False,
                "reason:": "Frame counts and persistence cannot be negative.",
            }

        # Persistence cannot exceed the number of observed frames.
        if (
            aggregated["persistence"]
            > aggregated["frame_count"]
        ).any():
            return {
                "valid": False,
                "reason": (
                    "Crowd persistence cannot exceed frame_count."
                ),
            }

        numeric_columns = [
            "average_people",
            "crowd_load",
            "movement_load",
            "spatial_load",
            "crowd_growth_per_sec",
            "growth_load",
            "frame_count",
            "persistence",
        ]

        if not np.isfinite(
            aggregated[numeric_columns].to_numpy()
        ).all():
            return {
                "valid": False,
                "reason": "Non-finite values detected.",
            }

        return {
            "valid": True,
            "window_count": int(
                len(aggregated)
            ),
            # Total observations, not crowd persistence.
            "frames_covered": int(
                aggregated["frame_count"].sum()
            ),
        }
