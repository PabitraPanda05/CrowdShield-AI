
"""
CrowdShield AI — Production Camera Source Abstraction

Provides a common interface for frame acquisition from:

    1. Recorded video files
    2. USB/web cameras
    3. RTSP/IP cameras

The AI pipeline should consume frames through this abstraction rather
than depending directly on cv2.VideoCapture.

IMPORTANT
---------
This module handles frame acquisition only.

It does not perform:

    object detection
    tracking
    crowd counting
    risk scoring
    response decisions
    routing

Those responsibilities remain inside the production AI pipeline.
"""

from __future__ import annotations

import time

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import cv2


# =====================================================================
# CAMERA CONFIGURATION
# =====================================================================

@dataclass
class CameraSourceConfig:

    source_type: str

    source: Union[str, int]

    name: str = "camera"

    expected_fps: Optional[float] = None

    reconnect_attempts: int = 3

    reconnect_delay_seconds: float = 2.0

    width: Optional[int] = None

    height: Optional[int] = None


# =====================================================================
# CAMERA FRAME
# =====================================================================

@dataclass
class CameraFrame:

    frame: Any

    frame_number: int

    timestamp_seconds: float

    source_name: str

    width: int

    height: int

    fps: float


# =====================================================================
# BASE CAMERA SOURCE
# =====================================================================

class CameraSource:

    """
    Base interface for production frame sources.
    """

    def __init__(
        self,
        config: CameraSourceConfig,
    ):

        self.config = config

        self.capture = None

        self.frame_number = 0

        self.started = False

        self.start_time = None

    # -----------------------------------------------------------------
    # OPEN
    # -----------------------------------------------------------------

    def open(self) -> bool:

        raise NotImplementedError

    # -----------------------------------------------------------------
    # READ
    # -----------------------------------------------------------------

    def read(self) -> Optional[CameraFrame]:

        raise NotImplementedError

    # -----------------------------------------------------------------
    # RELEASE
    # -----------------------------------------------------------------

    def release(self) -> None:

        if self.capture is not None:

            self.capture.release()

        self.capture = None

        self.started = False

    # -----------------------------------------------------------------
    # CONTEXT MANAGER
    # -----------------------------------------------------------------

    def __enter__(self):

        self.open()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        self.release()

    # -----------------------------------------------------------------
    # STATUS
    # -----------------------------------------------------------------

    def is_opened(self) -> bool:

        return (
            self.capture is not None
            and self.capture.isOpened()
        )

    # -----------------------------------------------------------------
    # METADATA
    # -----------------------------------------------------------------

    def metadata(self) -> Dict[str, Any]:

        if self.capture is None:

            return {
                "opened": False,
                "source_name": self.config.name,
            }

        return {
            "opened": self.is_opened(),

            "source_type":
                self.config.source_type,

            "source":
                str(self.config.source),

            "source_name":
                self.config.name,

            "frame_number":
                self.frame_number,

            "fps":
                self._get_fps(),

            "width":
                self._get_width(),

            "height":
                self._get_height(),
        }

    # -----------------------------------------------------------------
    # INTERNAL METADATA HELPERS
    # -----------------------------------------------------------------

    def _get_fps(self) -> float:

        if self.capture is None:

            return 0.0

        fps = float(
            self.capture.get(
                cv2.CAP_PROP_FPS
            )
        )

        return fps if fps > 0 else 0.0

    def _get_width(self) -> int:

        if self.capture is None:

            return 0

        return int(
            self.capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

    def _get_height(self) -> int:

        if self.capture is None:

            return 0

        return int(
            self.capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )


# =====================================================================
# OPENCV CAMERA SOURCE
# =====================================================================

class OpenCVCameraSource(CameraSource):

    """
    OpenCV-based camera source.

    Supports:

        video file
        USB camera index
        RTSP URL
        IP camera URL
    """

    def open(self) -> bool:

        self.release()

        source = self.config.source

        self.capture = cv2.VideoCapture(
            source
        )

        if not self.capture.isOpened():

            self.capture.release()

            self.capture = None

            return False

        # -------------------------------------------------------------
        # Optional resolution configuration
        # -------------------------------------------------------------

        if self.config.width is not None:

            self.capture.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                self.config.width,
            )

        if self.config.height is not None:

            self.capture.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                self.config.height,
            )

        self.frame_number = 0

        self.start_time = time.perf_counter()

        self.started = True

        return True

    def read(
        self,
    ) -> Optional[CameraFrame]:

        if not self.is_opened():

            return None

        success, frame = (
            self.capture.read()
        )

        if not success:

            return None

        self.frame_number += 1

        fps = self._get_fps()

        if fps > 0:

            timestamp = (
                (self.frame_number - 1)
                / fps
            )

        elif self.start_time is not None:

            timestamp = (
                time.perf_counter()
                - self.start_time
            )

        else:

            timestamp = 0.0

        height, width = (
            frame.shape[:2]
        )

        return CameraFrame(
            frame=frame,

            frame_number=self.frame_number,

            timestamp_seconds=float(
                timestamp
            ),

            source_name=self.config.name,

            width=int(width),

            height=int(height),

            fps=float(fps),
        )


# =====================================================================
# FACTORY
# =====================================================================

def create_camera_source(
    config: CameraSourceConfig,
) -> CameraSource:

    """
    Create the correct camera source implementation.

    Currently OpenCV provides the common acquisition backend for:

        video
        USB
        RTSP
        IP cameras
    """

    source_type = (
        config.source_type
        .strip()
        .lower()
    )

    supported_types = {
        "video",
        "recorded_video",
        "usb",
        "webcam",
        "rtsp",
        "ip_camera",
        "camera",
    }

    if source_type not in supported_types:

        raise ValueError(
            "Unsupported camera source type: "
            f"{config.source_type}. "
            f"Supported types: "
            f"{sorted(supported_types)}"
        )

    return OpenCVCameraSource(
        config
    )


# =====================================================================
# CAMERA SOURCE VALIDATION
# =====================================================================

def validate_camera_config(
    config: CameraSourceConfig,
) -> Dict[str, Any]:

    errors = []

    if not config.name:

        errors.append(
            "Camera name cannot be empty."
        )

    if config.reconnect_attempts < 0:

        errors.append(
            "Reconnect attempts cannot be negative."
        )

    if config.reconnect_delay_seconds < 0:

        errors.append(
            "Reconnect delay cannot be negative."
        )

    source_type = (
        config.source_type
        .strip()
        .lower()
    )

    if source_type in {
        "video",
        "recorded_video",
    }:

        source_path = Path(
            str(config.source)
        )

        if not source_path.exists():

            errors.append(
                "Video source does not exist: "
                f"{source_path}"
            )

        elif not source_path.is_file():

            errors.append(
                "Video source is not a file: "
                f"{source_path}"
            )

    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
    }
