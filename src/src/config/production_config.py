
"""
CrowdShield AI — Centralized Production Configuration

All production-level model, risk, routing, camera and pipeline
parameters should be defined here.

IMPORTANT
---------
These parameters are engineering configuration values.

They are NOT calibrated probabilities and do not represent
safety-certified thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple


# =====================================================================
# PROJECT PATHS
# =====================================================================

PROJECT_ROOT = Path(
    r"C:\Users\pabit\CrowdShield-AI"
)

YOLO_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "yolo"
    / "crowd_detection.pt"
)

DEFAULT_VIDEO_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "videos"
    / "people.mp4.mp4"
)


# =====================================================================
# YOLO CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class YOLOConfig:

    confidence: float = 0.25
    iou: float = 0.45
    device: str | None = None


# =====================================================================
# BYTE TRACK CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class ByteTrackConfig:

    track_high_thresh: float = 0.25
    track_low_thresh: float = 0.10
    new_track_thresh: float = 0.25
    track_buffer: int = 30
    match_thresh: float = 0.80


# =====================================================================
# CROWD INTELLIGENCE CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class CrowdConfig:

    frame_width: int = 1920
    frame_height: int = 1080


# =====================================================================
# RISK FEATURE CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class RiskFeatureConfig:

    reference_crowd_count: float = 13.0

    reference_speed_px_per_sec: float = 1000.0

    reference_spatial_spread: float = 0.50

    movement_event_speed_px_per_sec: float = 750.0

    crowd_growth_reference_per_sec: float = 2.0


# =====================================================================
# TEMPORAL CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class TemporalConfig:

    window_seconds: float = 1.0


# =====================================================================
# OPERATIONAL RISK CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class OperationalRiskConfig:

    crowd_weight: float = 0.25

    movement_weight: float = 0.15

    movement_event_weight: float = 0.20

    spatial_weight: float = 0.10

    growth_weight: float = 0.15

    persistence_weight: float = 0.15

    low_threshold: float = 25.0

    moderate_threshold: float = 50.0

    high_threshold: float = 70.0


# =====================================================================
# RESPONSE CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class ResponseConfig:

    rising_growth_threshold: float = 0.50

    high_risk_threshold: float = 50.0

    human_review_required: bool = True

    autonomous_emergency_action: bool = False


# =====================================================================
# ROUTING CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class RoutingConfig:

    risk_weight: float = 8.0

    distance_weight: float = 1.0

    allow_diagonal: bool = False


# =====================================================================
# CAMERA CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class CameraConfig:

    default_source: str = "recorded_video"

    default_fps: float = 25.0

    reconnect_attempts: int = 3

    reconnect_delay_seconds: float = 2.0

    frame_width: int = 1920

    frame_height: int = 1080


# =====================================================================
# PIPELINE CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class PipelineConfig:

    batch_size: int = 1

    enable_tracking: bool = True

    enable_risk_analysis: bool = True

    enable_response_decisions: bool = True

    enable_routing: bool = True

    save_frame_features: bool = True

    save_temporal_windows: bool = True

    save_operational_risk: bool = True

    save_response_decisions: bool = True


# =====================================================================
# COMPLETE PRODUCTION CONFIGURATION
# =====================================================================

@dataclass(frozen=True)
class ProductionConfig:

    project_root: Path = PROJECT_ROOT

    yolo_model_path: Path = YOLO_MODEL_PATH

    default_video_path: Path = DEFAULT_VIDEO_PATH

    yolo: YOLOConfig = field(
        default_factory=YOLOConfig
    )

    bytetrack: ByteTrackConfig = field(
        default_factory=ByteTrackConfig
    )

    crowd: CrowdConfig = field(
        default_factory=CrowdConfig
    )

    risk_features: RiskFeatureConfig = field(
        default_factory=RiskFeatureConfig
    )

    temporal: TemporalConfig = field(
        default_factory=TemporalConfig
    )

    operational_risk: OperationalRiskConfig = field(
        default_factory=OperationalRiskConfig
    )

    response: ResponseConfig = field(
        default_factory=ResponseConfig
    )

    routing: RoutingConfig = field(
        default_factory=RoutingConfig
    )

    camera: CameraConfig = field(
        default_factory=CameraConfig
    )

    pipeline: PipelineConfig = field(
        default_factory=PipelineConfig
    )


# =====================================================================
# DEFAULT CONFIGURATION INSTANCE
# =====================================================================

PRODUCTION_CONFIG = ProductionConfig()


# =====================================================================
# VALIDATION
# =====================================================================

def validate_config(
    config: ProductionConfig = PRODUCTION_CONFIG,
) -> Tuple[bool, list[str]]:

    errors: list[str] = []

    # -------------------------------------------------------------
    # Paths
    # -------------------------------------------------------------

    if not config.project_root.exists():

        errors.append(
            "Project root does not exist."
        )

    if not config.yolo_model_path.exists():

        errors.append(
            "YOLO model file does not exist."
        )

    # -------------------------------------------------------------
    # YOLO
    # -------------------------------------------------------------

    if not (
        0.0
        <= config.yolo.confidence
        <= 1.0
    ):

        errors.append(
            "YOLO confidence must be in [0,1]."
        )

    if not (
        0.0
        <= config.yolo.iou
        <= 1.0
    ):

        errors.append(
            "YOLO IoU must be in [0,1]."
        )

    # -------------------------------------------------------------
    # ByteTrack
    # -------------------------------------------------------------

    if config.bytetrack.track_buffer <= 0:

        errors.append(
            "ByteTrack track_buffer must be > 0."
        )

    if not (
        0.0
        <= config.bytetrack.match_thresh
        <= 1.0
    ):

        errors.append(
            "ByteTrack match_thresh must be in [0,1]."
        )

    # -------------------------------------------------------------
    # Risk references
    # -------------------------------------------------------------

    if config.risk_features.reference_crowd_count <= 0:

        errors.append(
            "reference_crowd_count must be > 0."
        )

    if (
        config.risk_features.reference_speed_px_per_sec
        <= 0
    ):

        errors.append(
            "reference_speed_px_per_sec must be > 0."
        )

    if (
        config.risk_features.reference_spatial_spread
        <= 0
    ):

        errors.append(
            "reference_spatial_spread must be > 0."
        )

    # -------------------------------------------------------------
    # Temporal
    # -------------------------------------------------------------

    if (
        config.temporal.window_seconds
        <= 0
    ):

        errors.append(
            "Temporal window must be > 0."
        )

    # -------------------------------------------------------------
    # Risk weights
    # -------------------------------------------------------------

    weights = [
        config.operational_risk.crowd_weight,
        config.operational_risk.movement_weight,
        config.operational_risk.movement_event_weight,
        config.operational_risk.spatial_weight,
        config.operational_risk.growth_weight,
        config.operational_risk.persistence_weight,
    ]

    if any(
        weight < 0
        for weight in weights
    ):

        errors.append(
            "Risk weights cannot be negative."
        )

    if abs(
        sum(weights) - 1.0
    ) > 1e-9:

        errors.append(
            "Operational risk weights must sum to 1.0."
        )

    # -------------------------------------------------------------
    # Risk thresholds
    # -------------------------------------------------------------

    if not (
        0
        <= config.operational_risk.low_threshold
        <
        config.operational_risk.moderate_threshold
        <
        config.operational_risk.high_threshold
        <= 100
    ):

        errors.append(
            "Operational risk thresholds are invalid."
        )

    # -------------------------------------------------------------
    # Response
    # -------------------------------------------------------------

    if (
        config.response.rising_growth_threshold
        < 0
    ):

        errors.append(
            "Response growth threshold cannot be negative."
        )

    if (
        config.response.high_risk_threshold
        < 0
    ):

        errors.append(
            "Response high-risk threshold cannot be negative."
        )

    # -------------------------------------------------------------
    # Routing
    # -------------------------------------------------------------

    if config.routing.risk_weight < 0:

        errors.append(
            "Routing risk weight cannot be negative."
        )

    if config.routing.distance_weight <= 0:

        errors.append(
            "Routing distance weight must be > 0."
        )

    # -------------------------------------------------------------
    # Camera
    # -------------------------------------------------------------

    if config.camera.default_fps <= 0:

        errors.append(
            "Camera FPS must be > 0."
        )

    if config.camera.reconnect_attempts < 0:

        errors.append(
            "Reconnect attempts cannot be negative."
        )

    if config.camera.reconnect_delay_seconds < 0:

        errors.append(
            "Reconnect delay cannot be negative."
        )

    # -------------------------------------------------------------
    # Pipeline
    # -------------------------------------------------------------

    if config.pipeline.batch_size <= 0:

        errors.append(
            "Pipeline batch_size must be > 0."
        )

    return (
        len(errors) == 0,
        errors,
    )
