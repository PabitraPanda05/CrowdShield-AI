from argparse import Namespace
from typing import Any, Dict, List

import numpy as np
from ultralytics.trackers.byte_tracker import BYTETracker


class ByteTrackPersonTracker:
    """
    Production ByteTrack wrapper compatible with
    Ultralytics 8.4.x and GPU YOLO inference.

    YOLO performs inference on the GPU.

    The native Ultralytics Boxes object is copied to CPU
    immediately before entering ByteTrack because the
    installed Ultralytics 8.4.161 tracker internally uses
    NumPy operations on bounding boxes.
    """

    def __init__(
        self,
        track_high_thresh: float = 0.25,
        track_low_thresh: float = 0.10,
        new_track_thresh: float = 0.25,
        track_buffer: int = 30,
        match_thresh: float = 0.80,
        frame_rate: int = 25,
    ):
        self.track_high_thresh = track_high_thresh
        self.track_low_thresh = track_low_thresh
        self.new_track_thresh = new_track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.frame_rate = frame_rate

        self._create_tracker()

    def _create_tracker(self) -> None:
        """
        Create ByteTrack using the constructor required
        by Ultralytics 8.4.x.
        """

        args = Namespace(
            track_high_thresh=self.track_high_thresh,
            track_low_thresh=self.track_low_thresh,
            new_track_thresh=self.new_track_thresh,
            track_buffer=self.track_buffer,
            match_thresh=self.match_thresh,
            fuse_score=True,
        )

        self.tracker = BYTETracker(args)

        self.frame_id = 0

    def reset(self) -> None:
        """
        Reset the complete tracking state.
        """

        self._create_tracker()

    def update(
        self,
        boxes: Any,
    ) -> List[Dict[str, Any]]:
        """
        Update ByteTrack using native Ultralytics Boxes.

        YOLO inference remains on GPU. The Boxes object is
        transferred to CPU only at this boundary because
        Ultralytics 8.4.161 performs NumPy operations inside
        its ByteTrack implementation.

        Parameters
        ----------
        boxes:
            Ultralytics engine.results.Boxes object.

        Returns
        -------
        List of tracked person dictionaries.
        """

        if boxes is None:
            return []

        required_attributes = [
            "conf",
            "cls",
            "xywh",
        ]

        missing = [
            attribute
            for attribute in required_attributes
            if not hasattr(boxes, attribute)
        ]

        if missing:
            raise TypeError(
                "ByteTrack requires a native Ultralytics "
                f"Boxes object with {missing}."
            )

        self.frame_id += 1

        # -------------------------------------------------------------
        # GPU → CPU boundary
        #
        # YOLO remains GPU accelerated.
        # Only the detection results are copied to CPU.
        # -------------------------------------------------------------

        boxes_cpu = boxes.cpu()

        # -------------------------------------------------------------
        # ByteTrack receives the native CPU Boxes object.
        # -------------------------------------------------------------

        tracks = self.tracker.update(
            boxes_cpu,
            img=None,
        )

        tracked_people: List[Dict[str, Any]] = []

        if tracks is None:
            return tracked_people

        tracks = np.asarray(tracks)

        if tracks.size == 0:
            return tracked_people

        if tracks.ndim == 1:
            tracks = tracks.reshape(1, -1)

        # -------------------------------------------------------------
        # Standard Ultralytics ByteTrack output:
        #
        # x1, y1, x2, y2, track_id, score, class_id, ...
        # -------------------------------------------------------------

        for track in tracks:

            if len(track) < 5:
                continue

            x1 = float(track[0])
            y1 = float(track[1])
            x2 = float(track[2])
            y2 = float(track[3])

            track_id = int(track[4])

            confidence = (
                float(track[5])
                if len(track) >= 6
                else 0.0
            )

            class_id = (
                int(track[6])
                if len(track) >= 7
                else 0
            )

            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0

            tracked_people.append(
                {
                    "track_id": track_id,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "center_x": center_x,
                    "center_y": center_y,
                    "confidence": confidence,
                    "class_id": class_id,
                }
            )

        return tracked_people

    @staticmethod
    def to_array(
        tracks: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Convert structured tracks to an Nx9 NumPy array.

        Columns:
            track_id
            x1
            y1
            x2
            y2
            center_x
            center_y
            confidence
            class_id
        """

        if not tracks:
            return np.empty(
                (0, 9),
                dtype=np.float32,
            )

        return np.asarray(
            [
                [
                    track["track_id"],
                    track["x1"],
                    track["y1"],
                    track["x2"],
                    track["y2"],
                    track["center_x"],
                    track["center_y"],
                    track["confidence"],
                    track["class_id"],
                ]
                for track in tracks
            ],
            dtype=np.float32,
        )
