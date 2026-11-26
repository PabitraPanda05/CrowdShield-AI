import threading
import time
from datetime import datetime
from dataclasses import replace
from typing import Any, Optional

from src.config.production_config import (
    PRODUCTION_CONFIG,
    YOLO_MODEL_PATH,
    validate_config,
)

from src.camera.camera_source import (
    CameraSourceConfig,
    OpenCVCameraSource,
)

from src.detection.yolo_detector import YOLOPersonDetector
from src.tracking.bytetrack_tracker import ByteTrackPersonTracker
from src.crowd.crowd_intelligence import CrowdIntelligenceEngine
from src.risk.risk_features import RiskFeatureEngine
from src.risk.temporal_aggregator import TemporalRiskAggregator
from src.risk.operational_risk import OperationalRiskEngine
from src.response.response_engine import ResponseDecisionEngine
from src.pipeline.production_pipeline import ProductionAIPipeline

from backend.services.database_service import database_service


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def utc_now() -> str:
    return datetime.now().astimezone().isoformat()


def last_record(data: Any) -> dict:
    """Convert a list or DataFrame's last record to a dictionary."""

    if data is None:
        return {}

    if hasattr(data, "empty") and hasattr(data, "iloc"):
        if data.empty:
            return {}
        return data.iloc[-1].to_dict()

    if isinstance(data, list):
        if data and isinstance(data[-1], dict):
            return data[-1]
        return {}

    if isinstance(data, dict):
        return data

    return {}


def safe_number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)

        if result != result or result in (
            float("inf"),
            float("-inf"),
        ):
            return default

        return result

    except (TypeError, ValueError):
        return default


def first_present(record: dict, keys: tuple, default=None):
    """Return the first non-empty value found in a record."""
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return default


def calculate_zone_occupancy(
    tracks: list,
    frame_width: int,
    frame_height: int,
    grid_size: int = 4,
) -> dict:
    """
    Count tracked-person bounding-box centres in a 4x4 image-space grid.

    This is an image-space occupancy estimate, not people per square metre.
    Track dictionaries are expected to contain x1, y1, x2 and y2.
    """
    width = max(1, int(frame_width or 1))
    height = max(1, int(frame_height or 1))
    occupancy = {
        f"r{row + 1}c{col + 1}": 0
        for row in range(grid_size)
        for col in range(grid_size)
    }

    if not isinstance(tracks, (list, tuple)):
        return occupancy

    for track in tracks:
        if not isinstance(track, dict):
            continue

        try:
            x1 = safe_number(track.get("x1"), None)
            y1 = safe_number(track.get("y1"), None)
            x2 = safe_number(track.get("x2"), None)
            y2 = safe_number(track.get("y2"), None)
            if None in (x1, y1, x2, y2):
                continue

            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0

            col = min(
                grid_size - 1,
                max(0, int(center_x / width * grid_size))
            )
            row = min(
                grid_size - 1,
                max(0, int(center_y / height * grid_size))
            )
            occupancy[f"r{row + 1}c{col + 1}"] += 1
        except (TypeError, ValueError, OverflowError):
            continue

    return occupancy



# ---------------------------------------------------------
# Camera source with FPS fallback
# ---------------------------------------------------------

class RuntimeCameraSource(OpenCVCameraSource):
    """
    Adds a fallback FPS value for cameras that report FPS = 0.
    """

    def read(self):
        camera_frame = super().read()

        if camera_frame is None:
            live_source_types = {
                "webcam",
                "usb",
                "rtsp",
                "ip_camera",
                "camera",
            }

            source_type = self.config.source_type.strip().lower()

            if source_type in live_source_types:
                attempts = max(0, int(self.config.reconnect_attempts))

                for _ in range(attempts):
                    if self.config.reconnect_delay_seconds > 0:
                        time.sleep(self.config.reconnect_delay_seconds)

                    if not self.open():
                        continue

                    camera_frame = super().read()

                    if camera_frame is not None:
                        break

        if camera_frame is None:
            return None

        if safe_number(camera_frame.fps) <= 0:
            fallback_fps = safe_number(
                self.config.expected_fps,
                PRODUCTION_CONFIG.camera.default_fps,
            )

            if fallback_fps <= 0:
                fallback_fps = 25.0

            camera_frame = replace(
                camera_frame,
                fps=fallback_fps,
            )

        return camera_frame


# ---------------------------------------------------------
# Camera worker
# ---------------------------------------------------------

class CameraWorker:
    """Runs one camera stream in its own background thread."""

    def __init__(
        self,
        camera_id: str,
        camera_name: str,
        source_type: str,
        source: Any,
        expected_fps: Optional[float] = None,
    ):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.source_type = source_type
        self.source = source

        self.expected_fps = safe_number(
            expected_fps or PRODUCTION_CONFIG.camera.default_fps,
            25.0,
        )

        if self.expected_fps <= 0:
            self.expected_fps = 25.0

        self.status = "CONNECTING"
        self.error = None
        self.width = 0
        self.height = 0
        self.fps = self.expected_fps
        self.frame_count = 0
        self.latest_frame = {}
        self.latest_raw_frame = None
        self.latest_risk = {}
        self.latest_response = {}
        self.last_updated = utc_now()

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread = None
        self._camera_source = None
        self._last_crowd_snapshot_at = 0.0
        self._crowd_snapshot_interval_seconds = 5.0

    def snapshot(self) -> dict:
        """Return a JSON-friendly camera status snapshot."""

        with self._lock:
            return {
                "camera_id": self.camera_id,
                "camera_name": self.camera_name,
                "source_type": self.source_type,
                "status": self.status,
                "live_stream": self.source_type in {
                    "webcam",
                    "usb",
                    "rtsp",
                    "ip_camera",
                    "camera",
                },
                "width": self.width,
                "height": self.height,
                "fps": round(self.fps, 2),
                "frame_count": self.frame_count,
                "latest_frame": dict(self.latest_frame),
                "latest_person_count": self.latest_frame.get(
                    "person_count", 0
                ),
                "latest_risk": dict(self.latest_risk),
                "latest_response": dict(self.latest_response),
                "error": self.error,
                "last_updated": self.last_updated,
            }

    def start(self):
        if self._thread and self._thread.is_alive():
            raise RuntimeError(
                f"Camera {self.camera_id} is already running."
            )

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name=f"crowdshield-camera-{self.camera_id}",
            daemon=True,
        )

        self._thread.start()

    def stop(self, timeout: float = 5.0):
        self._stop_event.set()

        with self._lock:
            self.status = "STOPPING"
            self.last_updated = utc_now()
            camera_source = self._camera_source

        # Releasing the capture can unblock a pending camera read.
        if camera_source is not None:
            try:
                camera_source.release()
            except Exception:
                pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

        with self._lock:
            if not self._thread or not self._thread.is_alive():
                self.status = "STOPPED"

            self.last_updated = utc_now()

    def _build_pipeline(self, width: int, height: int):
        """Construct independent AI state for this camera."""

        config = PRODUCTION_CONFIG

        detector = YOLOPersonDetector(
            model_path=str(YOLO_MODEL_PATH),
            confidence=config.yolo.confidence,
            iou=config.yolo.iou,
            device=config.yolo.device,
        )

        tracker_config = config.bytetrack

        tracker = ByteTrackPersonTracker(
            track_high_thresh=tracker_config.track_high_thresh,
            track_low_thresh=tracker_config.track_low_thresh,
            new_track_thresh=tracker_config.new_track_thresh,
            track_buffer=tracker_config.track_buffer,
            match_thresh=tracker_config.match_thresh,
            frame_rate=max(1, int(round(self.expected_fps))),
        )

        crowd_engine = CrowdIntelligenceEngine(
            frame_width=max(1, width),
            frame_height=max(1, height),
        )

        risk_config = config.risk_features

        risk_engine = RiskFeatureEngine(
            reference_crowd_count=risk_config.reference_crowd_count,
            reference_speed_px_per_sec=(
                risk_config.reference_speed_px_per_sec
            ),
            reference_spatial_spread=(
                risk_config.reference_spatial_spread
            ),
            movement_event_speed_px_per_sec=(
                risk_config.movement_event_speed_px_per_sec
            ),
            crowd_growth_reference_per_sec=(
                risk_config.crowd_growth_reference_per_sec
            ),
        )

        temporal_engine = TemporalRiskAggregator(
            fps=self.expected_fps,
            window_seconds=config.temporal.window_seconds,
        )

        operational_config = config.operational_risk

        operational_engine = OperationalRiskEngine(
            weights={
                "crowd": operational_config.crowd_weight,
                "movement": operational_config.movement_weight,
                "movement_event": (
                    operational_config.movement_event_weight
                ),
                "spatial": operational_config.spatial_weight,
                "growth": operational_config.growth_weight,
                "persistence": operational_config.persistence_weight,
            },
            moderate_threshold=operational_config.low_threshold,
            high_threshold=operational_config.moderate_threshold,
            critical_threshold=operational_config.high_threshold,
        )

        response_config = config.response

        response_engine = ResponseDecisionEngine(
            rising_growth_threshold=(
                response_config.rising_growth_threshold
            ),
            high_risk_threshold=response_config.high_risk_threshold,
        )

        return ProductionAIPipeline(
            detector=detector,
            tracker=tracker,
            crowd_engine=crowd_engine,
            risk_feature_engine=risk_engine,
            temporal_aggregator=temporal_engine,
            operational_engine=operational_engine,
            response_engine=response_engine,
        )

    def _run(self):
        camera_source = None

        try:
            valid, errors = validate_config(PRODUCTION_CONFIG)

            if not valid:
                raise RuntimeError(
                    "Production configuration is invalid: "
                    + "; ".join(str(error) for error in errors)
                )

            camera_config = CameraSourceConfig(
                source_type=self.source_type,
                source=self.source,
                name=self.camera_name,
                expected_fps=self.expected_fps,
                reconnect_attempts=(
                    PRODUCTION_CONFIG.camera.reconnect_attempts
                ),
                reconnect_delay_seconds=(
                    PRODUCTION_CONFIG.camera.reconnect_delay_seconds
                ),
                width=PRODUCTION_CONFIG.camera.frame_width,
                height=PRODUCTION_CONFIG.camera.frame_height,
            )

            camera_source = RuntimeCameraSource(camera_config)

            with self._lock:
                self._camera_source = camera_source

            if not camera_source.open():
                raise RuntimeError(
                    "Unable to open camera source. Check the webcam "
                    "index, RTSP URL, network, and camera permissions."
                )

            if self._stop_event.is_set():
                return

            # Read a frame to obtain the actual camera dimensions.
            first_frame = camera_source.read()

            if first_frame is None:
                raise RuntimeError(
                    "Camera opened but did not provide a readable frame."
                )

            self.width = first_frame.width
            self.height = first_frame.height
            self.fps = safe_number(
                first_frame.fps,
                self.expected_fps,
            )

            # Build the pipeline using the camera's dimensions.
            pipeline = self._build_pipeline(
                self.width,
                self.height,
            )

            with self._lock:
                self.status = "RUNNING"
                self.error = None
                self.last_updated = utc_now()

            # Preserve the detector, tracker and risk-engine state
            # across batches.
            while not self._stop_event.is_set():
                # Reopen a live source before entering the production
                # pipeline if the previous connection was lost.
                if not camera_source.is_opened():
                    live_source_types = {
                        "webcam",
                        "usb",
                        "rtsp",
                        "ip_camera",
                        "camera",
                    }

                    source_type = self.source_type.strip().lower()

                    if source_type not in live_source_types:
                        raise RuntimeError(
                            "Camera source is not open."
                        )

                    attempts = max(
                        1,
                        int(
                            PRODUCTION_CONFIG.camera.reconnect_attempts
                        ),
                    )

                    reconnected = False

                    with self._lock:
                        self.status = "CONNECTING"
                        self.error = "Camera source disconnected; reconnecting."
                        self.last_updated = utc_now()

                    while not self._stop_event.is_set() and not reconnected:
                        for _ in range(attempts):
                            if self._stop_event.is_set():
                                break

                            if PRODUCTION_CONFIG.camera.reconnect_delay_seconds > 0:
                                time.sleep(
                                    PRODUCTION_CONFIG.camera.reconnect_delay_seconds
                                )

                            if self._stop_event.is_set():
                                break

                            if camera_source.open():
                                reconnected = True
                                break

                        if not reconnected and not self._stop_event.is_set():
                            with self._lock:
                                self.status = "CONNECTING"
                                self.error = "Camera source unavailable; retrying connection."
                                self.last_updated = utc_now()

                    if self._stop_event.is_set():
                        break

                    with self._lock:
                        self.status = "RUNNING"
                        self.error = None
                        self.last_updated = utc_now()

                result = pipeline.process_camera(
                    camera_source,
                    max_frames=25,
                    collect_results=True,
                )

                if self._stop_event.is_set():
                    break

                frame_results = result.get("frame_results", [])

                latest_frame_result = (
                    frame_results[-1] if frame_results else {}
                )

                crowd = latest_frame_result.get("crowd", {}) or {}
                detections = latest_frame_result.get("detections", [])
                tracks = latest_frame_result.get("tracks", [])

                # Ultralytics detections may be a Boxes object,
                # not a Python list or tuple.
                try:
                    detection_count = (
                        len(detections)
                        if detections is not None
                        else 0
                    )
                except (TypeError, AttributeError):
                    detection_count = 0

                if isinstance(tracks, (list, tuple)):
                    track_count = len(tracks)
                else:
                    track_count = 0

                risk_record = last_record(
                    result.get("operational_risk")
                )

                response_record = last_record(
                    result.get("response_decisions")
                )

                person_count = crowd.get(
                    "person_count",
                    crowd.get("crowd_count", track_count),
                )

                def serialize_overlay_records(records):
                    """Convert detection and tracking records to JSON-safe dictionaries."""

                    allowed_fields = {
                        "track_id",
                        "x1",
                        "y1",
                        "x2",
                        "y2",
                        "center_x",
                        "center_y",
                        "confidence",
                        "class_id",
                        "class_name",
                    }

                    serialized = []

                    if not isinstance(records, (list, tuple)):
                        return serialized

                    for record in records:
                        if not isinstance(record, dict):
                            continue

                        item = {}

                        for key in allowed_fields:
                            value = record.get(key)

                            if value is None:
                                continue

                            if isinstance(value, (int, float, str, bool)):
                                item[key] = value

                        if all(
                            key in item
                            for key in ("x1", "y1", "x2", "y2")
                        ):
                            serialized.append(item)

                    return serialized

                safe_detections = serialize_overlay_records(detections)
                safe_tracks = serialize_overlay_records(tracks)


                # Persist one historical snapshot every five seconds.
                # Reuse this batch's existing YOLO + ByteTrack results;
                # no additional camera connection or detection pass is created.
                now_monotonic = time.monotonic()
                if (
                    frame_results
                    and now_monotonic - self._last_crowd_snapshot_at
                    >= self._crowd_snapshot_interval_seconds
                ):
                    try:
                        risk_score_value = first_present(
                            risk_record,
                            (
                                "risk_score",
                                "operational_risk_score",
                                "risk_index",
                                "score",
                            ),
                            None,
                        )
                        risk_level_value = first_present(
                            risk_record,
                            (
                                "risk_level",
                                "operational_risk_level",
                                "risk_category",
                                "level",
                            ),
                            None,
                        )

                        zone_occupancy = calculate_zone_occupancy(
                            safe_tracks,
                            self.width,
                            self.height,
                            grid_size=4,
                        )

                        database_service.save_crowd_snapshot(
                            camera_id=self.camera_id,
                            camera_name=self.camera_name,
                            person_count=int(
                                max(0, safe_number(person_count))
                            ),
                            risk_score=(
                                safe_number(risk_score_value)
                                if risk_score_value is not None
                                else None
                            ),
                            risk_level=(
                                str(risk_level_value)
                                if risk_level_value is not None
                                else None
                            ),
                            zone_occupancy=zone_occupancy,
                        )

                        self._last_crowd_snapshot_at = now_monotonic

                    except Exception as snapshot_error:
                        # Historical logging must never stop live monitoring.
                        print(
                            f"[CROWD HISTORY] Failed to save snapshot "
                            f"for {self.camera_id}: {snapshot_error}"
                        )

                with self._lock:
                    self.frame_count += len(frame_results)

                    if result.get("latest_raw_frame") is not None:
                        self.latest_raw_frame = result["latest_raw_frame"].copy()

                    if latest_frame_result:
                        self.latest_frame = {
                            "frame_number": latest_frame_result.get(
                                "frame_number"
                            ),
                            "timestamp_seconds": safe_number(
                                latest_frame_result.get(
                                    "timestamp_seconds"
                                )
                            ),
                            "person_count": int(
                                safe_number(person_count)
                            ),
                            "detection_count": detection_count,
                            "track_count": track_count,
                            "detections": safe_detections,
                            "tracks": safe_tracks,
                            "frame_width": self.width,
                            "frame_height": self.height,
                            "crowd": {
                                key: value
                                for key, value in crowd.items()
                                if isinstance(
                                    value,
                                    (str, int, float, bool, list, dict),
                                ) or value is None
                            },
                        }

                    self.latest_risk = {
                        key: value
                        for key, value in risk_record.items()
                        if isinstance(
                            value,
                            (str, int, float, bool),
                        ) or value is None
                    }

                    self.latest_response = {
                        key: value
                        for key, value in response_record.items()
                        if isinstance(
                            value,
                            (str, int, float, bool),
                        ) or value is None
                    }

                    self.last_updated = utc_now()

                # An empty batch can indicate that the stream stopped.
                # Keep the worker alive for live sources so the existing
                # camera can reconnect without requiring re-registration.
                if not frame_results:
                    live_source_types = {
                        "webcam",
                        "usb",
                        "rtsp",
                        "ip_camera",
                        "camera",
                    }

                    source_type = self.source_type.strip().lower()

                    if source_type not in live_source_types:
                        raise RuntimeError(
                            "Camera returned no processed frames."
                        )

                    attempts = max(
                        1,
                        int(
                            PRODUCTION_CONFIG.camera.reconnect_attempts
                        ),
                    )

                    reconnected = False

                    with self._lock:
                        self.status = "CONNECTING"
                        self.error = "Camera stream interrupted; reconnecting."
                        self.last_updated = utc_now()

                    for _ in range(attempts):
                        if self._stop_event.is_set():
                            break

                        if PRODUCTION_CONFIG.camera.reconnect_delay_seconds > 0:
                            time.sleep(
                                PRODUCTION_CONFIG.camera.reconnect_delay_seconds
                            )

                        if self._stop_event.is_set():
                            break

                        if camera_source.open():
                            reconnected = True
                            break

                    if self._stop_event.is_set():
                        break

                    if not reconnected:
                        raise RuntimeError(
                            "Camera stream interrupted and reconnect failed."
                        )

                    with self._lock:
                        self.status = "RUNNING"
                        self.error = None
                        self.last_updated = utc_now()

                    continue

        except Exception as exc:
            with self._lock:
                if not self._stop_event.is_set():
                    self.status = "ERROR"
                    self.error = str(exc)

                self.last_updated = utc_now()

        finally:
            if camera_source is not None:
                try:
                    camera_source.release()
                except Exception:
                    pass

            with self._lock:
                self._camera_source = None

                if self._stop_event.is_set():
                    self.status = "STOPPED"

                self.last_updated = utc_now()


# ---------------------------------------------------------
# Camera service manager
# ---------------------------------------------------------

class CameraService:
    """Manages multiple independent camera workers."""

    SUPPORTED_TYPES = {
        "webcam",
        "usb",
        "rtsp",
        "ip_camera",
        "camera",
    }

    def __init__(self):
        self._workers = {}
        self._lock = threading.RLock()

    def start_camera(
        self,
        camera_id: str,
        source_type: str,
        source: Any,
        camera_name: Optional[str] = None,
        expected_fps: Optional[float] = None,
    ) -> dict:
        camera_id = str(camera_id).strip()
        source_type = str(source_type).strip().lower()

        if not camera_id:
            raise ValueError("camera_id cannot be empty.")

        if source_type not in self.SUPPORTED_TYPES:
            raise ValueError(
                "Unsupported source_type. Use webcam, usb, rtsp, "
                "ip_camera, or camera."
            )

        if source is None or str(source).strip() == "":
            raise ValueError(
                "A camera index or stream URL is required."
            )

        if source_type in {"webcam", "usb", "camera"}:
            try:
                source = int(source)
            except (ValueError, TypeError):
                raise ValueError(
                    "For webcam/USB sources, provide a camera index "
                    "such as 0 or 1."
                )

        with self._lock:
            existing = self._workers.get(camera_id)

            if existing and existing.snapshot()["status"] in {
                "CONNECTING",
                "RUNNING",
                "STOPPING",
            }:
                raise ValueError(
                    f"Camera {camera_id} is already active."
                )

            worker = CameraWorker(
                camera_id=camera_id,
                camera_name=camera_name or camera_id,
                source_type=source_type,
                source=source,
                expected_fps=expected_fps,
            )

            self._workers[camera_id] = worker
            worker.start()

        return worker.snapshot()

    def get_camera(self, camera_id: str) -> Optional[dict]:
        with self._lock:
            worker = self._workers.get(str(camera_id))

        return worker.snapshot() if worker else None

    def get_camera_worker(self, camera_id: str) -> Optional[CameraWorker]:
        with self._lock:
            return self._workers.get(str(camera_id))

    def get_cameras(self) -> list:
        with self._lock:
            workers = list(self._workers.values())

        return [
            worker.snapshot()
            for worker in sorted(
                workers,
                key=lambda item: item.camera_id,
            )
        ]

    def stop_camera(self, camera_id: str) -> dict:
        with self._lock:
            worker = self._workers.get(str(camera_id))

        if worker is None:
            raise ValueError(
                f"Camera {camera_id} was not found."
            )

        worker.stop()
        return worker.snapshot()

    def stop_all(self):
        with self._lock:
            workers = list(self._workers.values())

        for worker in workers:
            worker.stop()


# Shared service instance for FastAPI endpoints.
camera_service = CameraService()