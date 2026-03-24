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
        / "prj-reviework"
        / "python"
    ),
)

from session_parser import SessionParser


class SessionParserAliasCompatibilityTest(unittest.TestCase):
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
            (session_dir / "video_frame_timestamps.csv").write_text(
                "camera_sensor_timestamp_ns,elapsed_realtime_ns,wall_time_ms,rotation_degrees,session_elapsed_ns\n1,2001,1001,0,1\n",
                encoding="utf-8",
            )
            (session_dir / "imu.csv").write_text(
                "sensor_type,event_timestamp_ns,elapsed_realtime_ns,wall_time_ms,x,y,z,accuracy\naccel,2002,2002,1002,0,0,0,3\n",
                encoding="utf-8",
            )
            (session_dir / "poses.jsonl").write_text('{"elapsedRealtimeNanos":2005}\n', encoding="utf-8")
            (session_dir / "bt.jsonl").write_text('{"elapsedRealtimeNanos":2004}\n', encoding="utf-8")

            parser = SessionParser(session_dir)
            summary = parser.load_summary()
            join_report = parser.build_join_report()

            self.assertEqual("review", summary.session_mode)
            self.assertEqual(1, summary.stream_counts["bt"])
            self.assertEqual(1, summary.stream_counts["poses"])
            self.assertTrue(join_report["metadataSufficiency"]["hasPoseTimeline"])
            self.assertFalse(join_report["metadataSufficiency"]["hasGnssTimeline"])


if __name__ == "__main__":
    unittest.main()
