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
    session_package_interface = parser.build_session_package_interface()

    output = {
        "summary": {
            "sessionId": summary.session_id,
            "status": summary.status,
            "deviceModel": summary.device_model,
            "sessionMode": summary.session_mode,
            "streamCounts": summary.stream_counts,
            "collectorStatus": summary.collector_status,
            "frameTimeRangeNs": summary.frame_time_range_ns,
            "imuTimeRangeNs": summary.imu_time_range_ns,
            "gnssTimeRangeNs": summary.gnss_time_range_ns,
            "btTimeRangeNs": summary.bt_time_range_ns,
            "poseTimeRangeNs": summary.pose_time_range_ns,
        },
        "joinReport": join_report,
        "sessionPackageInterface": {
            "requiredInputs": session_package_interface.required_inputs,
            "optionalInputs": session_package_interface.optional_inputs,
            "derivedOutputs": session_package_interface.derived_outputs,
            "missingRequiredInputs": session_package_interface.missing_required_inputs,
            "readyForDiagnose": session_package_interface.ready_for_diagnose,
        },
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
