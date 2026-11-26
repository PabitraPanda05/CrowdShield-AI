
"""
CrowdShield AI — Production Health Checks

Provides reusable readiness and health checks for:

    configuration
    model files
    video/camera sources
    Python dependencies
    GPU availability
    production pipeline components

Health checks are intended for:

    FastAPI
    monitoring
    deployment validation
    startup checks
    diagnostics

IMPORTANT
---------
A HEALTHY result means the corresponding technical component is
available and functioning according to the implemented checks.

It does NOT mean the AI system is safety-certified or that a scene
is safe.
"""

from __future__ import annotations

import importlib
import platform
import time

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


# =====================================================================
# HEALTH RESULT
# =====================================================================

@dataclass
class HealthResult:

    name: str

    status: str

    message: str

    details: Dict[str, Any]

    duration_ms: float


VALID_STATUSES = {
    "HEALTHY",
    "DEGRADED",
    "UNHEALTHY",
}


def _result(
    name: str,
    status: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    started_at: Optional[float] = None,
) -> HealthResult:

    if status not in VALID_STATUSES:

        raise ValueError(
            f"Invalid health status: {status}"
        )

    if details is None:

        details = {}

    duration_ms = 0.0

    if started_at is not None:

        duration_ms = (
            time.perf_counter()
            - started_at
        ) * 1000.0

    return HealthResult(
        name=name,
        status=status,
        message=message,
        details=details,
        duration_ms=duration_ms,
    )


# =====================================================================
# FILE CHECK
# =====================================================================

def check_file(
    name: str,
    path: Path,
) -> HealthResult:

    started = time.perf_counter()

    path = Path(path)

    if not path.exists():

        return _result(
            name=name,
            status="UNHEALTHY",
            message="Required file does not exist.",
            details={
                "path": str(path),
            },
            started_at=started,
        )

    if not path.is_file():

        return _result(
            name=name,
            status="UNHEALTHY",
            message="Expected file path is not a file.",
            details={
                "path": str(path),
            },
            started_at=started,
        )

    size_bytes = (
        path.stat().st_size
    )

    if size_bytes <= 0:

        return _result(
            name=name,
            status="UNHEALTHY",
            message="File exists but is empty.",
            details={
                "path": str(path),
                "size_bytes": size_bytes,
            },
            started_at=started,
        )

    return _result(
        name=name,
        status="HEALTHY",
        message="File is available.",
        details={
            "path": str(path),
            "size_bytes": size_bytes,
        },
        started_at=started,
    )


# =====================================================================
# DIRECTORY CHECK
# =====================================================================

def check_directory(
    name: str,
    path: Path,
) -> HealthResult:

    started = time.perf_counter()

    path = Path(path)

    if not path.exists():

        return _result(
            name=name,
            status="UNHEALTHY",
            message="Required directory does not exist.",
            details={
                "path": str(path),
            },
            started_at=started,
        )

    if not path.is_dir():

        return _result(
            name=name,
            status="UNHEALTHY",
            message="Expected directory path is not a directory.",
            details={
                "path": str(path),
            },
            started_at=started,
        )

    return _result(
        name=name,
        status="HEALTHY",
        message="Directory is available.",
        details={
            "path": str(path),
        },
        started_at=started,
    )


# =====================================================================
# PYTHON DEPENDENCY CHECK
# =====================================================================

def check_dependency(
    module_name: str,
) -> HealthResult:

    started = time.perf_counter()

    try:

        module = importlib.import_module(
            module_name
        )

        version = getattr(
            module,
            "__version__",
            "unknown",
        )

        return _result(
            name=f"dependency:{module_name}",
            status="HEALTHY",
            message="Python dependency is importable.",
            details={
                "module": module_name,
                "version": str(version),
            },
            started_at=started,
        )

    except Exception as exc:

        return _result(
            name=f"dependency:{module_name}",
            status="UNHEALTHY",
            message="Python dependency could not be imported.",
            details={
                "module": module_name,
                "error": str(exc),
            },
            started_at=started,
        )


# =====================================================================
# GPU CHECK
# =====================================================================

def check_gpu() -> HealthResult:

    started = time.perf_counter()

    try:

        import torch

    except Exception as exc:

        return _result(
            name="gpu",
            status="UNHEALTHY",
            message="PyTorch is unavailable.",
            details={
                "error": str(exc),
            },
            started_at=started,
        )

    cuda_available = bool(
        torch.cuda.is_available()
    )

    if not cuda_available:

        return _result(
            name="gpu",
            status="DEGRADED",
            message="CUDA GPU is not available; CPU execution may be used.",
            details={
                "cuda_available": False,
                "torch_version": str(
                    torch.__version__
                ),
            },
            started_at=started,
        )

    device_count = int(
        torch.cuda.device_count()
    )

    device_name = str(
        torch.cuda.get_device_name(0)
    )

    cuda_version = str(
        torch.version.cuda
    )

    return _result(
        name="gpu",
        status="HEALTHY",
        message="CUDA GPU is available.",
        details={
            "cuda_available": True,
            "device_count": device_count,
            "device_name": device_name,
            "cuda_version": cuda_version,
            "torch_version": str(
                torch.__version__
            ),
        },
        started_at=started,
    )


# =====================================================================
# VIDEO SOURCE CHECK
# =====================================================================

def check_video_source(
    path: Path,
) -> HealthResult:

    started = time.perf_counter()

    path = Path(path)

    if not path.exists():

        return _result(
            name="video_source",
            status="UNHEALTHY",
            message="Video source does not exist.",
            details={
                "path": str(path),
            },
            started_at=started,
        )

    try:

        import cv2

        cap = cv2.VideoCapture(
            str(path)
        )

        if not cap.isOpened():

            cap.release()

            return _result(
                name="video_source",
                status="UNHEALTHY",
                message="Video source could not be opened.",
                details={
                    "path": str(path),
                },
                started_at=started,
            )

        frame_count = int(
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

        ret, _ = cap.read()

        cap.release()

        if not ret:

            return _result(
                name="video_source",
                status="UNHEALTHY",
                message="Video opened but a frame could not be read.",
                details={
                    "path": str(path),
                    "frame_count": frame_count,
                    "fps": fps,
                },
                started_at=started,
            )

        if (
            frame_count <= 0
            or fps <= 0
            or width <= 0
            or height <= 0
        ):

            return _result(
                name="video_source",
                status="DEGRADED",
                message="Video opened but metadata is incomplete.",
                details={
                    "path": str(path),
                    "frame_count": frame_count,
                    "fps": fps,
                    "width": width,
                    "height": height,
                },
                started_at=started,
            )

        return _result(
            name="video_source",
            status="HEALTHY",
            message="Video source is readable.",
            details={
                "path": str(path),
                "frame_count": frame_count,
                "fps": fps,
                "width": width,
                "height": height,
            },
            started_at=started,
        )

    except Exception as exc:

        return _result(
            name="video_source",
            status="UNHEALTHY",
            message="Video source health check failed.",
            details={
                "path": str(path),
                "error": str(exc),
            },
            started_at=started,
        )


# =====================================================================
# CONFIGURATION CHECK
# =====================================================================

def check_configuration() -> HealthResult:

    started = time.perf_counter()

    try:

        from src.config.production_config import (
            PRODUCTION_CONFIG,
            validate_config,
        )

        valid, errors = (
            validate_config(
                PRODUCTION_CONFIG
            )
        )

        if not valid:

            return _result(
                name="configuration",
                status="UNHEALTHY",
                message="Production configuration is invalid.",
                details={
                    "errors": errors,
                },
                started_at=started,
            )

        return _result(
            name="configuration",
            status="HEALTHY",
            message="Production configuration is valid.",
            details={
                "project_root": str(
                    PRODUCTION_CONFIG.project_root
                ),
                "yolo_model": str(
                    PRODUCTION_CONFIG.yolo_model_path
                ),
            },
            started_at=started,
        )

    except Exception as exc:

        return _result(
            name="configuration",
            status="UNHEALTHY",
            message="Configuration check failed.",
            details={
                "error": str(exc),
            },
            started_at=started,
        )


# =====================================================================
# PRODUCTION MODULE CHECK
# =====================================================================

def check_production_module(
    module_name: str,
    required_class: str,
) -> HealthResult:

    started = time.perf_counter()

    try:

        module = importlib.import_module(
            module_name
        )

        if not hasattr(
            module,
            required_class,
        ):

            return _result(
                name=f"module:{module_name}",
                status="UNHEALTHY",
                message="Required class is missing.",
                details={
                    "module": module_name,
                    "required_class":
                        required_class,
                },
                started_at=started,
            )

        return _result(
            name=f"module:{module_name}",
            status="HEALTHY",
            message="Production module is importable.",
            details={
                "module": module_name,
                "class": required_class,
            },
            started_at=started,
        )

    except Exception as exc:

        return _result(
            name=f"module:{module_name}",
            status="UNHEALTHY",
            message="Production module could not be imported.",
            details={
                "module": module_name,
                "class": required_class,
                "error": str(exc),
            },
            started_at=started,
        )


# =====================================================================
# COMPLETE SYSTEM HEALTH CHECK
# =====================================================================

def run_system_health_check(
    project_root: Optional[Path] = None,
    video_path: Optional[Path] = None,
) -> Dict[str, Any]:

    if project_root is None:

        project_root = Path(
            r"C:\Users\pabit\CrowdShield-AI"
        )

    project_root = Path(
        project_root
    )

    if video_path is None:

        video_path = (
            project_root
            / "data"
            / "raw"
            / "videos"
            / "people.mp4.mp4"
        )

    video_path = Path(
        video_path
    )

    checks: List[
        HealthResult
    ] = []

    # -------------------------------------------------------------
    # Core paths
    # -------------------------------------------------------------

    checks.append(
        check_directory(
            "project_root",
            project_root,
        )
    )

    checks.append(
        check_directory(
            "logs",
            project_root / "logs",
        )
    )

    # -------------------------------------------------------------
    # Model
    # -------------------------------------------------------------

    checks.append(
        check_file(
            "yolo_model",
            (
                project_root
                / "models"
                / "yolo"
                / "crowd_detection.pt"
            ),
        )
    )

    # -------------------------------------------------------------
    # Video
    # -------------------------------------------------------------

    checks.append(
        check_video_source(
            video_path
        )
    )

    # -------------------------------------------------------------
    # Dependencies
    # -------------------------------------------------------------

    dependencies = [
        "cv2",
        "numpy",
        "pandas",
        "torch",
        "ultralytics",
    ]

    for dependency in dependencies:

        checks.append(
            check_dependency(
                dependency
            )
        )

    # -------------------------------------------------------------
    # GPU
    # -------------------------------------------------------------

    checks.append(
        check_gpu()
    )

    # -------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------

    checks.append(
        check_configuration()
    )

    # -------------------------------------------------------------
    # Production modules
    # -------------------------------------------------------------

    production_modules = [
        (
            "src.detection.yolo_detector",
            "YOLOPersonDetector",
        ),
        (
            "src.tracking.bytetrack_tracker",
            "ByteTrackPersonTracker",
        ),
        (
            "src.crowd.crowd_intelligence",
            "CrowdIntelligenceEngine",
        ),
        (
            "src.risk.risk_features",
            "RiskFeatureEngine",
        ),
        (
            "src.risk.temporal_aggregator",
            "TemporalRiskAggregator",
        ),
        (
            "src.risk.operational_risk",
            "OperationalRiskEngine",
        ),
        (
            "src.response.response_engine",
            "ResponseDecisionEngine",
        ),
        (
            "src.routing.risk_aware_router",
            "RiskAwareRouter",
        ),
        (
            "src.pipeline.production_pipeline",
            "ProductionAIPipeline",
        ),
    ]

    for module_name, class_name in (
        production_modules
    ):

        checks.append(
            check_production_module(
                module_name,
                class_name,
            )
        )

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------

    healthy = sum(
        result.status == "HEALTHY"
        for result in checks
    )

    degraded = sum(
        result.status == "DEGRADED"
        for result in checks
    )

    unhealthy = sum(
        result.status == "UNHEALTHY"
        for result in checks
    )

    if unhealthy > 0:

        overall_status = "UNHEALTHY"

    elif degraded > 0:

        overall_status = "DEGRADED"

    else:

        overall_status = "HEALTHY"

    return {
        "status": overall_status,

        "summary": {
            "total": len(checks),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
        },

        "checks": [
            asdict(result)
            for result in checks
        ],
    }


# =====================================================================
# READINESS CHECK
# =====================================================================

def is_system_ready(
    health_report: Dict[str, Any],
) -> bool:

    """
    Return True only when no health check is unhealthy.

    DEGRADED is allowed because, for example, the system may operate
    on CPU when CUDA is unavailable.
    """

    return (
        health_report.get(
            "status"
        )
        != "UNHEALTHY"
    )
