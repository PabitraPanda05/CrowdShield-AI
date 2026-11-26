
"""
CrowdShield AI — Unified Production AI Pipeline

Pipeline
--------
Frame
  ↓
YOLO Detection
  ↓
ByteTrack Tracking
  ↓
Crowd Intelligence
  ↓
Risk Features
  ↓
Temporal Aggregation
  ↓
Operational Risk
  ↓
Response Decision

The pipeline is designed as a central orchestration layer so that
FastAPI, Streamlit and Flutter/React clients can consume the same
AI-processing logic.

IMPORTANT
---------
This pipeline is decision-support infrastructure.

It is not:
- a safety guarantee
- a calibrated probability model
- an autonomous emergency-control system
- a validated real-world evacuation system
"""

from __future__ import annotations
import time

from pathlib import Path
from src.camera.camera_source import CameraSource, CameraFrame

from typing import Any, Dict, List, Optional

import cv2
import pandas as pd


class ProductionAIPipeline:
    """
    Unified production AI pipeline.

    The pipeline owns orchestration only.

    Individual AI components remain responsible for:
        detection
        tracking
        crowd intelligence
        risk features
        temporal aggregation
        operational risk
        response decisions
    """

    def __init__(
        self,
        detector,
        tracker,
        crowd_engine,
        risk_feature_engine,
        temporal_aggregator,
        operational_engine,
        response_engine,
        router=None,
    ) -> None:

        self.detector = detector
        self.tracker = tracker
        self.crowd_engine = crowd_engine
        self.risk_feature_engine = (
            risk_feature_engine
        )
        self.temporal_aggregator = (
            temporal_aggregator
        )
        self.operational_engine = (
            operational_engine
        )
        self.response_engine = (
            response_engine
        )
        self.router = router

    # -----------------------------------------------------------------
    # Process one frame
    # -----------------------------------------------------------------

    def process_frame(
        self,
        frame,
        frame_number: int,
        timestamp_seconds: float,
        fps: float,
    ) -> Dict[str, Any]:

        if frame is None:
            raise ValueError(
                "Frame cannot be None."
            )

        # -------------------------------------------------------------
        # Detection
        # -------------------------------------------------------------

        boxes = (
            self.detector.detect_boxes(
                frame
            )
        )

        # -------------------------------------------------------------
        # Tracking
        # -------------------------------------------------------------

        tracks = (
            self.tracker.update(
                boxes
            )
        )

        # -------------------------------------------------------------
        # Crowd intelligence
        # -------------------------------------------------------------

        crowd_record = (
            self.crowd_engine.analyze_frame(
                tracks=tracks,
                frame_number=frame_number,
                timestamp_seconds=timestamp_seconds,
                fps=fps,
            )
        )

        # -------------------------------------------------------------
        # Risk features
        # -------------------------------------------------------------

        risk_record = (
            self.risk_feature_engine.extract(
                crowd_record
            )
        )

        # -------------------------------------------------------------
        # Normalize the frame-level production schema.
        #
        # The risk feature engine owns risk calculations, while the
        # pipeline owns orchestration metadata such as frame number
        # and timestamp.
        # -------------------------------------------------------------

        risk_record = dict(risk_record)

        risk_record.setdefault(
            "frame_number",
            frame_number,
        )

        risk_record.setdefault(
            "timestamp_seconds",
            timestamp_seconds,
        )

        return {
            "frame_number": frame_number,
            "timestamp_seconds": timestamp_seconds,
            "detections": boxes,
            "tracks": tracks,
            "crowd": crowd_record,
            "risk": risk_record,
        }

    # -----------------------------------------------------------------
    # Process complete video
    # -----------------------------------------------------------------

    def process_video(
        self,
        video_path,
        max_frames: Optional[int] = None,
    ) -> Dict[str, Any]:

        video_path = Path(
            video_path
        )

        if not video_path.exists():
            raise FileNotFoundError(
                f"Video not found: {video_path}"
            )

        cap = cv2.VideoCapture(
            str(video_path)
        )

        if not cap.isOpened():
            raise RuntimeError(
                f"Could not open video: {video_path}"
            )

        total_frames = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        fps = float(
            cap.get(
                cv2.CAP_PROP_FPS
            )
        )

        width = int(
            cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        if fps <= 0:
            cap.release()

            raise RuntimeError(
                "Invalid video FPS."
            )

        frame_records: List[
            Dict[str, Any]
        ] = []

        frames_processed = 0
        frames_with_tracks = 0

        while True:

            if (
                max_frames is not None
                and
                frames_processed >= max_frames
            ):
                break

            ret, frame = cap.read()

            if not ret:
                break

            frames_processed += 1

            timestamp_seconds = (
                (frames_processed - 1)
                / fps
            )

            result = self.process_frame(
                frame=frame,
                frame_number=frames_processed,
                timestamp_seconds=timestamp_seconds,
                fps=fps,
            )

            tracks = result[
                "tracks"
            ]

            if tracks:
                frames_with_tracks += 1

            frame_risk = dict(
                result["risk"]
            )

            frame_risk.setdefault(
                "frame_number",
                result["frame_number"],
            )

            frame_risk.setdefault(
                "timestamp_seconds",
                result["timestamp_seconds"],
            )

            frame_records.append(
                frame_risk
            )

        cap.release()

        if not frame_records:
            raise RuntimeError(
                "No frames were processed."
            )

        # -------------------------------------------------------------
        # Frame-level risk DataFrame
        # -------------------------------------------------------------

        frame_df = pd.DataFrame(
            frame_records
        )

        # -------------------------------------------------------------
        # Temporal aggregation
        # -------------------------------------------------------------

        window_df = (
            self.temporal_aggregator.aggregate(
                frame_features=frame_df
            )
        )

        # -------------------------------------------------------------
        # Operational risk
        # -------------------------------------------------------------

        risk_records = (
            self.operational_engine.calculate_batch(
                window_df.to_dict(
                    orient="records"
                )
            )
        )

        risk_df = pd.DataFrame(
            risk_records
        )

        # -------------------------------------------------------------
        # Response decisions
        # -------------------------------------------------------------

        response_records = (
            self.response_engine.decide_batch(
                risk_df.to_dict(
                    orient="records"
                )
            )
        )

        response_df = pd.DataFrame(
            response_records
        )

        return {
            "metadata": {
                "video_path": str(
                    video_path
                ),
                "total_frames": total_frames,
                "frames_processed":
                    frames_processed,
                "fps": fps,
                "width": width,
                "height": height,
                "frames_with_tracks":
                    frames_with_tracks,
                "risk_windows":
                    len(window_df),
                "response_decisions":
                    len(response_df),
            },

            "frame_features":
                frame_df,

            "temporal_windows":
                window_df,

            "operational_risk":
                risk_df,

            "response_decisions":
                response_df,
        }

    # -----------------------------------------------------------------
    # Process a batch of frames
    # -----------------------------------------------------------------


    def process_camera(
        self,
        camera_source: CameraSource,
        max_frames: int | None = None,
        collect_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Process frames from a production CameraSource.

        Camera acquisition is handled by CameraSource.
        AI inference remains inside the production pipeline.

        The method follows the same downstream orchestration as
        process_video() and process_frames():

            frame processing
                ↓
            temporal aggregation
                ↓
            operational risk
                ↓
            response decisions

        This keeps camera-driven execution consistent with the
        validated production video pipeline.
        """

        if not camera_source.is_opened():
            raise RuntimeError(
                "Camera source is not open."
            )

        frame_results = []

        frame_records = []

        processed_frames = 0
        frames_with_tracks = 0
        latest_raw_frame = None

        started_at = time.perf_counter()

        while True:

            if (
                max_frames is not None
                and processed_frames >= max_frames
            ):
                break

            camera_frame = camera_source.read()

            if camera_frame is None:
                break

            processed_frames += 1
            latest_raw_frame = camera_frame.frame

            # ---------------------------------------------------------
            # Camera metadata
            # ---------------------------------------------------------

            frame_number = (
                camera_frame.frame_number
            )

            timestamp_seconds = (
                camera_frame.timestamp_seconds
            )

            fps = float(
                camera_frame.fps
            )

            if fps <= 0:
                raise RuntimeError(
                    "Camera source returned invalid FPS."
                )

            # ---------------------------------------------------------
            # Existing production frame-processing path
            # ---------------------------------------------------------

            result = self.process_frame(
                frame=camera_frame.frame,
                frame_number=frame_number,
                timestamp_seconds=timestamp_seconds,
                fps=fps,
            )

            # ---------------------------------------------------------
            # Normalize result metadata
            # ---------------------------------------------------------

            result = dict(result)

            result.setdefault(
                "frame_number",
                frame_number,
            )

            result.setdefault(
                "timestamp_seconds",
                timestamp_seconds,
            )

            result.setdefault(
                "source_name",
                camera_frame.source_name,
            )

            result.setdefault(
                "source_width",
                camera_frame.width,
            )

            result.setdefault(
                "source_height",
                camera_frame.height,
            )

            result.setdefault(
                "source_fps",
                camera_frame.fps,
            )

            # ---------------------------------------------------------
            # Track statistics
            # ---------------------------------------------------------

            tracks = result.get(
                "tracks",
                []
            )

            if tracks:
                frames_with_tracks += 1

            # ---------------------------------------------------------
            # Collect frame-level risk features
            # ---------------------------------------------------------

            frame_risk = dict(
                result["risk"]
            )

            frame_risk.setdefault(
                "frame_number",
                frame_number,
            )

            frame_risk.setdefault(
                "timestamp_seconds",
                timestamp_seconds,
            )

            frame_records.append(
                frame_risk
            )

            if collect_results:
                frame_results.append(
                    result
                )

        elapsed_seconds = (
            time.perf_counter()
            - started_at
        )

        if not frame_records:
            raise RuntimeError(
                "No frames were processed from camera source."
            )

        # -------------------------------------------------------------
        # Frame-level DataFrame
        # -------------------------------------------------------------

        frame_df = pd.DataFrame(
            frame_records
        )

        # -------------------------------------------------------------
        # Temporal aggregation
        # -------------------------------------------------------------

        window_df = (
            self.temporal_aggregator.aggregate(
                frame_features=frame_df
            )
        )

        # -------------------------------------------------------------
        # Operational risk
        # -------------------------------------------------------------

        risk_records = (
            self.operational_engine.calculate_batch(
                window_df.to_dict(
                    orient="records"
                )
            )
        )

        risk_df = pd.DataFrame(
            risk_records
        )

        # -------------------------------------------------------------
        # Response decisions
        # -------------------------------------------------------------

        response_records = (
            self.response_engine.decide_batch(
                risk_df.to_dict(
                    orient="records"
                )
            )
        )

        response_df = pd.DataFrame(
            response_records
        )

        # -------------------------------------------------------------
        # Latest operational state
        # -------------------------------------------------------------

        latest_state = (
            self.latest_state(
                response_df
            )
        )

        # -------------------------------------------------------------
        # Throughput
        # -------------------------------------------------------------

        throughput_fps = 0.0

        if elapsed_seconds > 0:
            throughput_fps = (
                processed_frames
                / elapsed_seconds
            )

        # -------------------------------------------------------------
        # Return complete production result
        # -------------------------------------------------------------

        return {
            "source": camera_source.metadata(),

            "processed_frames":
                processed_frames,

            "frames_with_tracks":
                frames_with_tracks,

            "processing_seconds":
                elapsed_seconds,

            "throughput_fps":
                throughput_fps,

            "frame_results":
                frame_results,

            "latest_raw_frame":
                latest_raw_frame,

            "frame_features":
                frame_df,

            "temporal_windows":
                window_df,

            "operational_risk":
                risk_df,

            "response_decisions":
                response_df,

            "latest_state":
                latest_state,
        }

    def process_frames(
        self,
        frames,
        fps: float,
    ) -> Dict[str, Any]:

        if fps <= 0:
            raise ValueError(
                "FPS must be greater than zero."
            )

        frame_records = []

        for index, frame in enumerate(
            frames,
            start=1,
        ):

            result = self.process_frame(
                frame=frame,
                frame_number=index,
                timestamp_seconds=(
                    (index - 1)
                    / fps
                ),
                fps=fps,
            )

            frame_risk = dict(
                result["risk"]
            )

            frame_risk.setdefault(
                "frame_number",
                result["frame_number"],
            )

            frame_risk.setdefault(
                "timestamp_seconds",
                result["timestamp_seconds"],
            )

            frame_records.append(
                frame_risk
            )

        if not frame_records:
            raise ValueError(
                "No frames supplied."
            )

        frame_df = pd.DataFrame(
            frame_records
        )

        window_df = (
            self.temporal_aggregator.aggregate(
                frame_features=frame_df
            )
        )

        risk_records = (
            self.operational_engine.calculate_batch(
                window_df.to_dict(
                    orient="records"
                )
            )
        )

        risk_df = pd.DataFrame(
            risk_records
        )

        response_records = (
            self.response_engine.decide_batch(
                risk_df.to_dict(
                    orient="records"
                )
            )
        )

        response_df = pd.DataFrame(
            response_records
        )

        return {
            "frame_features":
                frame_df,

            "temporal_windows":
                window_df,

            "operational_risk":
                risk_df,

            "response_decisions":
                response_df,
        }

    # -----------------------------------------------------------------
    # Latest operational state
    # -----------------------------------------------------------------

    @staticmethod
    def latest_state(
        response_df: pd.DataFrame,
    ) -> Dict[str, Any]:

        if response_df.empty:
            raise ValueError(
                "Response DataFrame is empty."
            )

        latest = response_df.iloc[-1]

        return {
            "window_id": int(
                latest["window_id"]
            ),

            "risk_score": float(
                latest[
                    "operational_risk_score"
                ]
            ),

            "risk_level": str(
                latest[
                    "operational_risk_level"
                ]
            ),

            "response_action": str(
                latest[
                    "response_action"
                ]
            ),

            "response_priority": str(
                latest[
                    "response_priority"
                ]
            ),

            "human_review_required": bool(
                latest[
                    "human_review_required"
                ]
            ),

            "autonomous_emergency_action":
                bool(
                    latest[
                        "autonomous_emergency_action"
                    ]
                ),
        }

