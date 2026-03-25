from __future__ import annotations

import json
import sys
from pathlib import Path

from session_parser import SessionParser


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python validate_session.py <session_dir>", file=sys.stderr)
        return 2

    session_dir = Path(sys.argv[1])
    parser = SessionParser(session_dir)
    summary = parser.load_summary()
    join_report = parser.build_join_report()

    output = {
        "summary": {
            "sessionId": summary.session_id,
            "status": summary.status,
            "deviceModel": summary.device_model,
            "streamCounts": summary.stream_counts,
            "collectorStatus": summary.collector_status,
            "frameTimeRangeNs": summary.frame_time_range_ns,
            "imuTimeRangeNs": summary.imu_time_range_ns,
            "gnssTimeRangeNs": summary.gnss_time_range_ns,
            "bleTimeRangeNs": summary.ble_time_range_ns,
            "arcoreTimeRangeNs": summary.arcore_time_range_ns,
        },
        "joinReport": join_report,
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
