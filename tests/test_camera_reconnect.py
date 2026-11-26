import unittest
from unittest.mock import patch
from src.camera.camera_source import CameraFrame, CameraSourceConfig, OpenCVCameraSource
from backend.services.camera_service import RuntimeCameraSource


class TestRuntimeCameraReconnect(unittest.TestCase):
    def test_live_camera_reconnects_after_failed_read(self):
        config = CameraSourceConfig(
            source_type="webcam",
            source=0,
            name="Test Webcam",
            expected_fps=25,
            reconnect_attempts=3,
            reconnect_delay_seconds=0,
        )

        source = RuntimeCameraSource(config)

        frame = CameraFrame(
            frame=None,
            frame_number=1,
            timestamp_seconds=0.0,
            source_name="Test Webcam",
            width=1280,
            height=720,
            fps=30.0,
        )

        with patch.object(
            OpenCVCameraSource,
            "read",
            side_effect=[None, frame],
        ) as mock_read:
            with patch.object(
                source,
                "open",
                return_value=True,
            ) as mock_open:
                result = source.read()

        self.assertIs(result, frame)
        self.assertEqual(mock_read.call_count, 2)
        self.assertEqual(mock_open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
