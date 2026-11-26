from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from ultralytics import YOLO


class YOLOPersonDetector:
    """
    Production wrapper for CrowdShield AI person detection.

    Responsibilities:
        - Load the validated YOLO model.
        - Run person detection on a frame.
        - Return structured detection records.
        - Keep model-specific logic isolated from the rest
          of the CrowdShield pipeline.
    """

    PERSON_CLASS_ID = 0

    def __init__(
        self,
        model_path: str,
        confidence: float = 0.25,
        iou: float = 0.45,
        device: Optional[str] = None,
    ):
        self.model_path = Path(model_path)
        self.confidence = confidence
        self.iou = iou
        self.device = device

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"YOLO model not found: {self.model_path}"
            )

        self.model = YOLO(str(self.model_path))

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect persons in a single BGR video frame.

        Returns:
            List of dictionaries containing:
                x1, y1, x2, y2
                confidence
                class_id
                class_name
        """

        if frame is None:
            raise ValueError("Input frame is None.")

        if not isinstance(frame, np.ndarray):
            raise TypeError("Input frame must be a NumPy array.")

        if frame.size == 0:
            raise ValueError("Input frame is empty.")

        predict_kwargs = {
            "source": frame,
            "conf": self.confidence,
            "iou": self.iou,
            "verbose": False,
        }

        if self.device is not None:
            predict_kwargs["device"] = self.device

        results = self.model.predict(**predict_kwargs)

        detections: List[Dict[str, Any]] = []

        if not results:
            return detections

        result = results[0]

        if result.boxes is None:
            return detections

        boxes = result.boxes

        xyxy = boxes.xyxy.cpu().numpy()
        confidences = boxes.conf.cpu().numpy()
        class_ids = boxes.cls.cpu().numpy().astype(int)

        names = result.names

        for box, confidence, class_id in zip(
            xyxy,
            confidences,
            class_ids,
        ):
            # CrowdShield operational pipeline currently focuses
            # specifically on person detections.
            if class_id != self.PERSON_CLASS_ID:
                continue

            x1, y1, x2, y2 = box.tolist()

            detections.append(
                {
                    "x1": float(x1),
                    "y1": float(y1),
                    "x2": float(x2),
                    "y2": float(y2),
                    "confidence": float(confidence),
                    "class_id": int(class_id),
                    "class_name": str(names[class_id]),
                }
            )

        return detections


    def detect_boxes(self, frame: np.ndarray):
        """
        Run YOLO detection and return the native Ultralytics
        Boxes object required by the installed ByteTrack API.

        This method intentionally preserves the native YOLO object
        because Ultralytics 8.4.x BYTETracker expects attributes such
        as:

            results.conf
            results.cls
            results.xywh

        Returns:
            Ultralytics Boxes object containing all detections.
        """

        if frame is None:
            raise ValueError("Input frame is None.")

        if not isinstance(frame, np.ndarray):
            raise TypeError(
                "Input frame must be a NumPy array."
            )

        if frame.size == 0:
            raise ValueError("Input frame is empty.")

        predict_kwargs = {
            "source": frame,
            "conf": self.confidence,
            "iou": self.iou,
            "verbose": False,
        }

        if self.device is not None:
            predict_kwargs["device"] = self.device

        results = self.model.predict(**predict_kwargs)

        if not results:
            return None

        result = results[0]

        if result.boxes is None:
            return None

        return result.boxes

    def detect_array(self, frame: np.ndarray) -> np.ndarray:
        """
        Convenience method returning detections as an Nx6 NumPy array.

        Columns:
            x1, y1, x2, y2, confidence, class_id
        """

        detections = self.detect(frame)

        if not detections:
            return np.empty((0, 6), dtype=np.float32)

        return np.asarray(
            [
                [
                    d["x1"],
                    d["y1"],
                    d["x2"],
                    d["y2"],
                    d["confidence"],
                    d["class_id"],
                ]
                for d in detections
            ],
            dtype=np.float32,
        )

    def count_persons(self, frame: np.ndarray) -> int:
        """
        Return the number of detected persons in a frame.
        """

        return len(self.detect(frame))
