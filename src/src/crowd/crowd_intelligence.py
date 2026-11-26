from typing import Any, Dict, List, Optional

import numpy as np

class CrowdIntelligenceEngine:
    """
    Production crowd-intelligence engine.

    Input:
        Tracked people from ByteTrack.

    Produces:
        - crowd count
        - spatial distribution
        - movement statistics
        - dominant crowd-flow direction
        - reverse-flow detection
        - potential bottleneck detection
        - frame-level crowd statistics

    This class intentionally does NOT calculate operational
    risk. Risk calculation belongs to the risk package.

    All movement measurements are image-space measurements.
    They are not calibrated physical walking speeds or densities.
    """

    # Movement threshold in image-space pixels per second.
    MOVEMENT_THRESHOLD = 20.0

    # Minimum number of moving tracks required to estimate
    # a reliable dominant crowd direction.
    MIN_FLOW_TRACKS = 2

    # Reverse movement must have cosine similarity below this.
    REVERSE_FLOW_COSINE_THRESHOLD = -0.5

    # Spatial grid configuration for bottleneck analysis.
    GRID_ROWS = 4
    GRID_COLS = 4

    # Minimum number of people in one grid cell.
    BOTTLENECK_MIN_PEOPLE = 3

    # Maximum average image-space speed for a potential
    # bottleneck cell.
    BOTTLENECK_MAX_SPEED = 30.0

    def __init__(
        self,
        frame_width: int,
        frame_height: int,
    ):
        if frame_width <= 0:
            raise ValueError(
                "frame_width must be greater than zero."
            )

        if frame_height <= 0:
            raise ValueError(
                "frame_height must be greater than zero."
            )

        self.frame_width = int(frame_width)
        self.frame_height = int(frame_height)

        # Previous center position for each tracked person.
        self.previous_positions: Dict[int, tuple] = {}

        # Previous frame number.
        self.previous_frame: Optional[int] = None

    # -----------------------------------------------------------------
    # Basic crowd count
    # -----------------------------------------------------------------

    @staticmethod
    def crowd_count(
        tracks: List[Dict[str, Any]]
    ) -> int:
        """
        Return the number of tracked people in the current frame.
        """

        return len(tracks)

    # -----------------------------------------------------------------
    # Spatial normalization
    # -----------------------------------------------------------------

    def normalized_position(
        self,
        center_x: float,
        center_y: float,
    ) -> tuple:
        """
        Convert pixel coordinates to normalized [0, 1] coordinates.
        """

        x = float(center_x) / self.frame_width
        y = float(center_y) / self.frame_height

        x = float(np.clip(x, 0.0, 1.0))
        y = float(np.clip(y, 0.0, 1.0))

        return x, y

    # -----------------------------------------------------------------
    # Spatial distribution
    # -----------------------------------------------------------------

    def spatial_distribution(
        self,
        tracks: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate normalized spatial distribution.
        """

        if not tracks:
            return {
                "mean_x": 0.0,
                "mean_y": 0.0,
                "std_x": 0.0,
                "std_y": 0.0,
                "min_x": 0.0,
                "max_x": 0.0,
                "min_y": 0.0,
                "max_y": 0.0,
            }

        positions = [
            self.normalized_position(
                track["center_x"],
                track["center_y"],
            )
            for track in tracks
        ]

        xs = np.asarray(
            [position[0] for position in positions],
            dtype=np.float32,
        )

        ys = np.asarray(
            [position[1] for position in positions],
            dtype=np.float32,
        )

        return {
            "mean_x": float(np.mean(xs)),
            "mean_y": float(np.mean(ys)),
            "std_x": float(np.std(xs)),
            "std_y": float(np.std(ys)),
            "min_x": float(np.min(xs)),
            "max_x": float(np.max(xs)),
            "min_y": float(np.min(ys)),
            "max_y": float(np.max(ys)),
        }

    # -----------------------------------------------------------------
    # Movement analysis
    # -----------------------------------------------------------------

    def movement_statistics(
        self,
        tracks: List[Dict[str, Any]],
        frame_number: int,
        fps: float,
    ) -> Dict[str, Any]:
        """
        Calculate frame-to-frame movement statistics.

        Movement is measured in pixels per second.

        Important:
            This is image-space movement, not physical walking speed.
        """

        if fps <= 0:
            raise ValueError(
                "fps must be greater than zero."
            )

        current_positions = {}

        speeds = []
        motion_vectors = []

        for track in tracks:

            track_id = int(track["track_id"])

            center_x = float(track["center_x"])
            center_y = float(track["center_y"])

            current_positions[track_id] = (
                center_x,
                center_y,
            )

            previous = self.previous_positions.get(
                track_id
            )

            if previous is None:
                continue

            dx = center_x - previous[0]
            dy = center_y - previous[1]

            distance_pixels = float(
                np.sqrt(
                    dx * dx
                    + dy * dy
                )
            )

            speed_pixels_per_second = (
                distance_pixels * fps
            )

            speeds.append(
                speed_pixels_per_second
            )

            motion_vectors.append({
                "track_id": track_id,
                "center_x": center_x,
                "center_y": center_y,
                "dx": dx,
                "dy": dy,
                "speed_px_per_sec": (
                    speed_pixels_per_second
                ),
            })

        self.previous_positions = current_positions
        self.previous_frame = frame_number

        if not speeds:
            return {
                "moving_tracks": 0,
                "mean_speed_px_per_sec": 0.0,
                "median_speed_px_per_sec": 0.0,
                "max_speed_px_per_sec": 0.0,
                "motion_vectors": [],
            }

        speed_array = np.asarray(
            speeds,
            dtype=np.float32,
        )

        moving_tracks = int(
            np.sum(
                speed_array >= self.MOVEMENT_THRESHOLD
            )
        )

        return {
            "moving_tracks": moving_tracks,

            "mean_speed_px_per_sec": float(
                np.mean(speed_array)
            ),

            "median_speed_px_per_sec": float(
                np.median(speed_array)
            ),

            "max_speed_px_per_sec": float(
                np.max(speed_array)
            ),

            "motion_vectors": motion_vectors,
        }

    # -----------------------------------------------------------------
    # Dominant crowd-flow and reverse-flow analysis
    # -----------------------------------------------------------------

    @staticmethod
    def direction_name(
        angle_degrees: float,
    ) -> str:
        """
        Convert a movement angle into one of eight directions.

        Image coordinate convention:
            X increases towards the right.
            Y increases towards the bottom.
        """

        directions = [
            "EAST",
            "SOUTH_EAST",
            "SOUTH",
            "SOUTH_WEST",
            "WEST",
            "NORTH_WEST",
            "NORTH",
            "NORTH_EAST",
        ]

        index = int(
            ((angle_degrees + 22.5) % 360) / 45.0
        )

        return directions[index]

    def flow_analysis(
        self,
        motion_vectors: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Estimate dominant crowd-flow direction and reverse flow.

        The most common directional sector is selected as the
        dominant flow. Tracks moving in approximately the opposite
        direction are classified as reverse-flow tracks.

        A minimum of MIN_FLOW_TRACKS is required.
        """

        moving_vectors = [
            vector
            for vector in motion_vectors
            if vector["speed_px_per_sec"]
            >= self.MOVEMENT_THRESHOLD
        ]

        empty_result = {
            "dominant_flow_direction": "UNKNOWN",
            "dominant_flow_angle": None,
            "flow_coherence": 0.0,
            "flow_track_count": 0,
            "reverse_flow_count": 0,
            "reverse_flow_ratio": 0.0,
        }

        if len(moving_vectors) < self.MIN_FLOW_TRACKS:
            return empty_result

        angles = np.asarray(
            [
                np.degrees(
                    np.arctan2(
                        vector["dy"],
                        vector["dx"],
                    )
                ) % 360.0
                for vector in moving_vectors
            ],
            dtype=np.float32,
        )

        # Divide movement into eight directional sectors.
        sector_indices = (
            np.floor(
                (angles + 22.5) / 45.0
            ).astype(int) % 8
        )

        sector_counts = np.bincount(
            sector_indices,
            minlength=8,
        )

        dominant_sector = int(
            np.argmax(sector_counts)
        )

        # Central angle of the dominant directional sector.
        dominant_angle = (
            dominant_sector * 45.0
        ) % 360.0

        dominant_radians = np.radians(
            dominant_angle
        )

        dominant_vector = np.asarray(
            [
                np.cos(dominant_radians),
                np.sin(dominant_radians),
            ],
            dtype=np.float32,
        )

        reverse_flow_count = 0
        aligned_count = 0

        for vector in moving_vectors:

            dx = float(vector["dx"])
            dy = float(vector["dy"])

            magnitude = float(
                np.sqrt(dx * dx + dy * dy)
            )

            if magnitude <= 0:
                continue

            unit_vector = np.asarray(
                [
                    dx / magnitude,
                    dy / magnitude,
                ],
                dtype=np.float32,
            )

            cosine_similarity = float(
                np.dot(
                    unit_vector,
                    dominant_vector,
                )
            )

            if (
                cosine_similarity
                <= self.REVERSE_FLOW_COSINE_THRESHOLD
            ):
                reverse_flow_count += 1

            if cosine_similarity >= 0.5:
                aligned_count += 1

        flow_coherence = (
            aligned_count / len(moving_vectors)
        )

        return {
            "dominant_flow_direction": (
                self.direction_name(dominant_angle)
            ),

            "dominant_flow_angle": float(
                dominant_angle
            ),

            "flow_coherence": float(
                flow_coherence
            ),

            "flow_track_count": len(
                moving_vectors
            ),

            "reverse_flow_count": int(
                reverse_flow_count
            ),

            "reverse_flow_ratio": float(
                reverse_flow_count
                / len(moving_vectors)
            ),
        }

    # -----------------------------------------------------------------
    # Potential bottleneck detection
    # -----------------------------------------------------------------

    def bottleneck_analysis(
        self,
        tracks: List[Dict[str, Any]],
        motion_vectors: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Identify potential bottleneck regions using a spatial grid.

        A grid cell is flagged when:
            1. It contains at least BOTTLENECK_MIN_PEOPLE.
            2. The average observed image-space speed is at or
               below BOTTLENECK_MAX_SPEED.

        This is a preliminary image-space indicator, not a
        physically calibrated bottleneck or safety diagnosis.
        """

        empty_result = {
            "potential_bottleneck_count": 0,
            "potential_bottleneck_zones": [],
        }

        if not tracks or not motion_vectors:
            return empty_result

        speed_by_track = {
            int(vector["track_id"]): float(
                vector["speed_px_per_sec"]
            )
            for vector in motion_vectors
        }

        grid = {}

        cell_width = (
            self.frame_width / self.GRID_COLS
        )

        cell_height = (
            self.frame_height / self.GRID_ROWS
        )

        for track in tracks:

            track_id = int(track["track_id"])

            # A speed measurement is needed to evaluate
            # movement inside the cell.
            if track_id not in speed_by_track:
                continue

            center_x = float(track["center_x"])
            center_y = float(track["center_y"])

            col = min(
                int(center_x / cell_width),
                self.GRID_COLS - 1,
            )

            row = min(
                int(center_y / cell_height),
                self.GRID_ROWS - 1,
            )

            cell_key = (row, col)

            if cell_key not in grid:
                grid[cell_key] = {
                    "people": 0,
                    "speeds": [],
                }

            grid[cell_key]["people"] += 1

            grid[cell_key]["speeds"].append(
                speed_by_track[track_id]
            )

        bottleneck_zones = []

        for (row, col), cell_data in grid.items():

            people_count = cell_data["people"]

            if (
                people_count
                < self.BOTTLENECK_MIN_PEOPLE
            ):
                continue

            average_speed = float(
                np.mean(cell_data["speeds"])
            )

            if (
                average_speed
                > self.BOTTLENECK_MAX_SPEED
            ):
                continue

            x_start = col / self.GRID_COLS
            y_start = row / self.GRID_ROWS

            x_end = (col + 1) / self.GRID_COLS
            y_end = (row + 1) / self.GRID_ROWS

            bottleneck_zones.append({
                "grid_row": int(row),
                "grid_col": int(col),

                "person_count": int(
                    people_count
                ),

                "mean_speed_px_per_sec": (
                    average_speed
                ),

                "region": {
                    "x_start": float(x_start),
                    "y_start": float(y_start),
                    "x_end": float(x_end),
                    "y_end": float(y_end),
                },
            })

        return {
            "potential_bottleneck_count": len(
                bottleneck_zones
            ),

            "potential_bottleneck_zones": (
                bottleneck_zones
            ),
        }

    # -----------------------------------------------------------------
    # Frame-level analysis
    # -----------------------------------------------------------------

    def analyze_frame(
        self,
        tracks: List[Dict[str, Any]],
        frame_number: int,
        timestamp_seconds: float,
        fps: float,
    ) -> Dict[str, Any]:
        """
        Generate the complete crowd-intelligence record
        for one video frame.
        """

        count = self.crowd_count(tracks)

        spatial = self.spatial_distribution(
            tracks
        )

        movement = self.movement_statistics(
            tracks=tracks,
            frame_number=frame_number,
            fps=fps,
        )

        flow = self.flow_analysis(
            movement["motion_vectors"]
        )

        bottlenecks = self.bottleneck_analysis(
            tracks=tracks,
            motion_vectors=movement["motion_vectors"],
        )

        return {
            "frame": int(frame_number),
            "time_seconds": float(timestamp_seconds),
            "person_count": int(count),

            # Existing spatial measurements.
            "mean_x": spatial["mean_x"],
            "mean_y": spatial["mean_y"],
            "std_x": spatial["std_x"],
            "std_y": spatial["std_y"],
            "min_x": spatial["min_x"],
            "max_x": spatial["max_x"],
            "min_y": spatial["min_y"],
            "max_y": spatial["max_y"],

            # Existing movement measurements.
            "moving_tracks": int(
                movement["moving_tracks"]
            ),

            "mean_speed_px_per_sec": (
                movement["mean_speed_px_per_sec"]
            ),

            "median_speed_px_per_sec": (
                movement["median_speed_px_per_sec"]
            ),

            "max_speed_px_per_sec": (
                movement["max_speed_px_per_sec"]
            ),

            # New crowd-flow measurements.
            "dominant_flow_direction": (
                flow["dominant_flow_direction"]
            ),

            "dominant_flow_angle": (
                flow["dominant_flow_angle"]
            ),

            "flow_coherence": (
                flow["flow_coherence"]
            ),

            "flow_track_count": (
                flow["flow_track_count"]
            ),

            "reverse_flow_count": (
                flow["reverse_flow_count"]
            ),

            "reverse_flow_ratio": (
                flow["reverse_flow_ratio"]
            ),

            # New bottleneck measurements.
            "potential_bottleneck_count": (
                bottlenecks[
                    "potential_bottleneck_count"
                ]
            ),

            "potential_bottleneck_zones": (
                bottlenecks[
                    "potential_bottleneck_zones"
                ]
            ),
        }

    # -----------------------------------------------------------------
    # Batch analysis
    # -----------------------------------------------------------------

    def analyze_frames(
        self,
        frame_tracks: Dict[int, List[Dict[str, Any]]],
        fps: float,
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple frames.

        Parameters
        ----------
        frame_tracks:
            Dictionary:
                frame_number -> list of tracks

        fps:
            Video frame rate.
        """

        if fps <= 0:
            raise ValueError(
                "fps must be greater than zero."
            )

        # Reset temporal state for a new sequence.
        self.previous_positions = {}
        self.previous_frame = None

        results = []

        for frame_number in sorted(
            frame_tracks.keys()
        ):

            timestamp_seconds = (
                frame_number - 1
            ) / fps

            result = self.analyze_frame(
                tracks=frame_tracks[frame_number],
                frame_number=frame_number,
                timestamp_seconds=timestamp_seconds,
                fps=fps,
            )

            results.append(result)

        return results