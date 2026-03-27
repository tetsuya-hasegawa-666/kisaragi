from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent.parent
        / "--products"
        / "prj-kisaragi_0002"
        / "python"
    ),
)

from session_parser import SessionParser


class SessionParserAliasCompatibilityTest(unittest.TestCase):
    def test_pose_coverage_ratio_uses_expected_arcore_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-20260327-pose-coverage"
            session_dir.mkdir(parents=True)

            manifest = {
                "sessionId": "session-20260327-pose-coverage",
                "status": "ready",
                "deviceModel": "Xperia 5 III",
                "sessionMode": "review",
                "timebase": {
                    "sessionStartWallTimeMs": 1000,
                    "sessionStartElapsedRealtimeNanos": 2000,
                },
                "recordingConfig": {
                    "arCoreEnabled": True,
                    "arCoreIntervalMs": 2000,
                },
            }
            (session_dir / "session_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (session_dir / "video.mp4").write_bytes(b"video")
            (session_dir / "video_frame_timestamps.csv").write_text(
                "camera_sensor_timestamp_ns,elapsed_realtime_ns,wall_time_ms,rotation_degrees,session_elapsed_ns\n"
                "1,0,1001,0,1\n"
                "2,1000000000,2001,0,2\n"
                "3,2000000000,3001,0,3\n"
                "4,3000000000,4001,0,4\n"
                "5,4000000000,5001,0,5\n",
                encoding="utf-8",
            )
            (session_dir / "imu.csv").write_text(
                "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                encoding="utf-8",
            )
            (session_dir / "bt.jsonl").write_text('{"elapsedRealtimeNanos":2004}\n', encoding="utf-8")
            (session_dir / "poses.jsonl").write_text(
                '{"elapsedRealtimeNanos":0}\n'
                '{"elapsedRealtimeNanos":2000000000}\n'
                '{"elapsedRealtimeNanos":4000000000}\n',
                encoding="utf-8",
            )

            parser = SessionParser(session_dir)
            session_package = parser.build_session_package_payload()

            self.assertEqual(1.0, session_package["scores"]["poseCoverageRatio"])

    def test_reviework_alias_fields_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-20260323-review"
            session_dir.mkdir(parents=True)

            manifest = {
                "sessionId": "session-20260323-review",
                "status": "ready",
                "deviceModel": "Xperia 5 III",
                "sessionMode": "review",
                "timebase": {
                    "sessionStartWallTimeMs": 1000,
                    "sessionStartElapsedRealtimeNanos": 2000,
                },
                "collectorStatus": {"intake": "complete"},
            }
            (session_dir / "session_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (session_dir / "video.mp4").write_bytes(b"video")
            (session_dir / "video_frame_timestamps.csv").write_text(
                "camera_sensor_timestamp_ns,elapsed_realtime_ns,wall_time_ms,rotation_degrees,session_elapsed_ns\n1,2001,1001,0,1\n",
                encoding="utf-8",
            )
            (session_dir / "imu.csv").write_text(
                "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                encoding="utf-8",
            )
            (session_dir / "poses.jsonl").write_text(
                '{"elapsedRealtimeNanos":2005,"frameTimestampNs":1005,"imageFocalLength":[1000.0,1001.0],"imagePrincipalPoint":[500.0,501.0],"imageDimensions":[1920,1080],"textureFocalLength":[998.0,999.0],"texturePrincipalPoint":[500.0,500.0],"textureDimensions":[1920,1080],"lensDistortion":[0.1,0.01,0.0,0.0,0.0]}\n',
                encoding="utf-8",
            )
            (session_dir / "bt.jsonl").write_text('{"elapsedRealtimeNanos":2004}\n', encoding="utf-8")

            parser = SessionParser(session_dir)
            summary = parser.load_summary()
            join_report = parser.build_join_report()
            package_interface = parser.build_session_package_interface()
            session_package = parser.build_session_package_payload()
            space_handoff_manifest = parser.build_space_handoff_manifest()

            self.assertEqual("review", summary.session_mode)
            self.assertEqual(1, summary.stream_counts["bt"])
            self.assertEqual(1, summary.stream_counts["poses"])
            self.assertTrue(join_report["metadataSufficiency"]["hasPoseTimeline"])
            self.assertFalse(join_report["metadataSufficiency"]["hasGnssTimeline"])
            self.assertTrue(package_interface.ready_for_diagnose)
            self.assertEqual([], package_interface.missing_required_inputs)
            self.assertIn("input_readiness.json", package_interface.derived_outputs)
            self.assertIn("camera_calibration_summary.json", package_interface.derived_outputs)
            self.assertEqual("video.mp4", session_package["sourceFiles"]["video"])
            self.assertEqual(1, session_package["cameraCalibration"]["imageIntrinsicsCount"])
            self.assertEqual(1, session_package["cameraCalibration"]["lensDistortionCount"])
            self.assertTrue(space_handoff_manifest["readyForSpaceReconstruction"])

    def test_session_package_interface_marks_missing_required_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-20260325-missing"
            session_dir.mkdir(parents=True)

            manifest = {
                "sessionId": "session-20260325-missing",
                "status": "draft",
                "deviceModel": "Xperia 5 III",
                "sessionMode": "review",
                "timebase": {
                    "sessionStartWallTimeMs": 1000,
                    "sessionStartElapsedRealtimeNanos": 2000,
                },
            }
            (session_dir / "session_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (session_dir / "video_frame_timestamps.csv").write_text(
                "camera_sensor_timestamp_ns,elapsed_realtime_ns,wall_time_ms,rotation_degrees,session_elapsed_ns\n1,2001,1001,0,1\n",
                encoding="utf-8",
            )

            parser = SessionParser(session_dir)
            package_interface = parser.build_session_package_interface()
            space_handoff_manifest = parser.build_space_handoff_manifest()

            self.assertFalse(package_interface.ready_for_diagnose)
            self.assertEqual(["video", "imu", "bt"], package_interface.missing_required_inputs)
            self.assertFalse(package_interface.optional_inputs["poses"])
            self.assertFalse(package_interface.optional_inputs["gnss"])
            self.assertFalse(space_handoff_manifest["readyForSpaceReconstruction"])
            self.assertIn("video.mp4 が不足している", space_handoff_manifest["blockers"])

    def test_legacy_csv_aliases_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-20260325-legacy"
            session_dir.mkdir(parents=True)

            manifest = {
                "sessionId": "session-20260325-legacy",
                "status": "ready",
                "deviceModel": "Xperia 5 III",
                "recordingMode": "review",
                "timebase": {
                    "sessionStartWallTimeMs": 1000,
                    "sessionStartElapsedRealtimeNanos": 2000,
                },
            }
            (session_dir / "session_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (session_dir / "video.mp4").write_bytes(b"video")
            (session_dir / "video_frame_timestamps.csv").write_text(
                "camera_sensor_timestamp_ns,elapsed_realtime_ns,wall_time_ms,rotation_degrees,session_elapsed_ns\n1,2001,1001,0,1\n",
                encoding="utf-8",
            )
            (session_dir / "imu.csv").write_text(
                "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                encoding="utf-8",
            )
            (session_dir / "bt_events.csv").write_text(
                "timestamp_ns,deviceAddress\n2004,AA:BB:CC:DD\n",
                encoding="utf-8",
            )
            (session_dir / "arcore_pose.csv").write_text(
                "timestamp_ns,tx,ty,tz\n2005,0,0,0\n",
                encoding="utf-8",
            )

            parser = SessionParser(session_dir)
            summary = parser.load_summary()
            join_report = parser.build_join_report()
            package_interface = parser.build_session_package_interface()
            session_package = parser.build_session_package_payload()

            self.assertEqual("review", summary.session_mode)
            self.assertEqual(1, summary.stream_counts["bt"])
            self.assertEqual(1, summary.stream_counts["poses"])
            self.assertEqual(3, join_report["btNearestDeltaNs"])
            self.assertEqual(4, join_report["poseNearestDeltaNs"])
            self.assertTrue(package_interface.ready_for_diagnose)
            self.assertEqual("bt_events.csv", session_package["sourceFiles"]["bt"])

    def test_manifest_frames_and_bt_csv_aliases_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-20260325-legacy-2"
            session_dir.mkdir(parents=True)

            manifest = {
                "sessionId": "session-20260325-legacy-2",
                "status": "ready",
                "deviceModel": "Xperia 5 III",
                "recordingMode": "review",
                "timebase": {
                    "sessionStartWallTimeMs": 1000,
                    "sessionStartElapsedRealtimeNanos": 2000,
                },
            }
            (session_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (session_dir / "video.mp4").write_bytes(b"video")
            (session_dir / "frames.csv").write_text(
                "frame_id,timestamp_ns\n0,2001\n",
                encoding="utf-8",
            )
            (session_dir / "imu.csv").write_text(
                "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                encoding="utf-8",
            )
            (session_dir / "bt.csv").write_text(
                "timestamp_ns,deviceAddress\n2004,AA:BB:CC:DD\n",
                encoding="utf-8",
            )
            (session_dir / "arcore_pose.csv").write_text(
                "timestamp_ns,tx,ty,tz\n2005,0,0,0\n",
                encoding="utf-8",
            )

            parser = SessionParser(session_dir)
            summary = parser.load_summary()
            package_interface = parser.build_session_package_interface()
            space_handoff_manifest = parser.build_space_handoff_manifest()

            self.assertEqual("session-20260325-legacy-2", summary.session_id)
            self.assertEqual(1, summary.stream_counts["frames"])
            self.assertEqual(1, summary.stream_counts["bt"])
            self.assertTrue(package_interface.ready_for_diagnose)
            self.assertTrue(space_handoff_manifest["readyForSpaceReconstruction"])


if __name__ == "__main__":
    unittest.main()
