from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionSummary:
    session_id: str
    status: str
    device_model: str
    session_mode: str
    session_dir: Path
    stream_counts: dict[str, int]
    collector_status: dict[str, str]
    frame_time_range_ns: tuple[int, int] | None
    imu_time_range_ns: tuple[int, int] | None
    gnss_time_range_ns: tuple[int, int] | None
    bt_time_range_ns: tuple[int, int] | None
    pose_time_range_ns: tuple[int, int] | None


@dataclass(frozen=True)
class SessionPackageInterface:
    required_inputs: dict[str, bool]
    optional_inputs: dict[str, bool]
    derived_outputs: dict[str, str]
    missing_required_inputs: list[str]
    ready_for_diagnose: bool


class SessionParser:
    def __init__(self, session_dir: str | Path) -> None:
        self.session_dir = Path(session_dir)
        self.manifest_path = self._find_first_existing("session_manifest.json", "manifest.json")
        if self.manifest_path is None:
            raise FileNotFoundError(f"Manifest not found under: {self.session_dir}")

        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.timebase = self.manifest["timebase"]

    def load_summary(self) -> SessionSummary:
        frame_rows = self.load_frame_rows()
        imu_rows = self.load_csv("imu.csv")
        gnss_rows = self.load_csv("gnss.csv")
        bt_rows = self.load_bt_rows()
        pose_rows = self.load_pose_rows()

        return SessionSummary(
            session_id=self.manifest["sessionId"],
            status=self.manifest["status"],
            device_model=self.manifest["deviceModel"],
            session_mode=self.manifest.get("sessionMode", self.manifest.get("recordingMode", self.manifest.get("recordingConfig", {}).get("recordingMode", "review"))),
            session_dir=self.session_dir,
            stream_counts={
                "frames": len(frame_rows),
                "imu": len(imu_rows),
                "gnss": len(gnss_rows),
                "bt": len(bt_rows),
                "poses": len(pose_rows),
            },
            collector_status=self.manifest.get("collectorStatus", {}),
            frame_time_range_ns=self._range_from_row_aliases(frame_rows, "elapsed_realtime_ns", "timestamp_ns"),
            imu_time_range_ns=self._range_from_rows(imu_rows, "elapsed_realtime_ns"),
            gnss_time_range_ns=self._range_from_rows(gnss_rows, "elapsed_realtime_ns"),
            bt_time_range_ns=self._range_from_row_aliases(bt_rows, "elapsedRealtimeNanos", "timestamp_ns"),
            pose_time_range_ns=self._range_from_row_aliases(pose_rows, "elapsedRealtimeNanos", "timestamp_ns"),
        )

    def load_csv(self, filename: str) -> list[dict[str, Any]]:
        path = self.session_dir / filename
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def load_jsonl(self, filename: str) -> list[dict[str, Any]]:
        path = self.session_dir / filename
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def load_jsonl_aliases(self, *filenames: str) -> list[dict[str, Any]]:
        for filename in filenames:
            rows = self.load_jsonl(filename)
            if rows:
                return rows
        return []

    def load_csv_aliases(self, *filenames: str) -> list[dict[str, Any]]:
        for filename in filenames:
            rows = self.load_csv(filename)
            if rows:
                return rows
        return []

    def _find_first_existing(self, *filenames: str) -> Path | None:
        for filename in filenames:
            path = self.session_dir / filename
            if path.exists():
                return path
        return None

    def load_frame_rows(self) -> list[dict[str, Any]]:
        return self.load_csv_aliases("video_frame_timestamps.csv", "frames.csv")

    def load_bt_rows(self) -> list[dict[str, Any]]:
        rows = self.load_jsonl_aliases("bt.jsonl", "ble_scan.jsonl")
        if rows:
            return rows
        return self.load_csv_aliases("bt_events.csv", "bt.csv")

    def load_pose_rows(self) -> list[dict[str, Any]]:
        rows = self.load_jsonl_aliases("poses.jsonl", "arcore_pose.jsonl")
        if rows:
            return rows
        return self.load_csv_aliases("arcore_pose.csv")

    def build_join_report(self) -> dict[str, Any]:
        frame_rows = self.load_frame_rows()
        imu_rows = self.load_csv("imu.csv")
        gnss_rows = self.load_csv("gnss.csv")
        bt_rows = self.load_bt_rows()
        pose_rows = self.load_pose_rows()

        return {
            "sessionId": self.manifest["sessionId"],
            "timebase": self.timebase,
            "frameCount": len(frame_rows),
            "imuNearestDeltaNs": self._nearest_delta_ns(frame_rows, imu_rows, ("elapsed_realtime_ns", "timestamp_ns")),
            "gnssNearestDeltaNs": self._nearest_delta_ns(frame_rows, gnss_rows, ("elapsed_realtime_ns", "timestamp_ns")),
            "btNearestDeltaNs": self._nearest_delta_ns(frame_rows, bt_rows, ("elapsedRealtimeNanos", "timestamp_ns")),
            "poseNearestDeltaNs": self._nearest_delta_ns(frame_rows, pose_rows, ("elapsedRealtimeNanos", "timestamp_ns")),
            "metadataSufficiency": {
                "hasMonotonicSessionBase": "sessionStartElapsedRealtimeNanos" in self.timebase,
                "hasWallClockBase": "sessionStartWallTimeMs" in self.timebase,
                "hasVideoFrameTimeline": len(frame_rows) > 0,
                "hasImuTimeline": len(imu_rows) > 0,
                "hasGnssTimeline": len(gnss_rows) > 0,
                "hasBtTimeline": len(bt_rows) > 0,
                "hasPoseTimeline": len(pose_rows) > 0,
                "hasCollectorStatus": bool(self.manifest.get("collectorStatus")),
            },
        }

    def build_session_package_interface(self) -> SessionPackageInterface:
        frame_rows = self.load_frame_rows()
        imu_rows = self.load_csv("imu.csv")
        gnss_rows = self.load_csv("gnss.csv")
        bt_rows = self.load_bt_rows()
        pose_rows = self.load_pose_rows()

        required_inputs = {
            "session_manifest": self.manifest_path is not None and self.manifest_path.exists(),
            "frames": len(frame_rows) > 0,
            "imu": len(imu_rows) > 0,
            "bt": len(bt_rows) > 0,
        }
        optional_inputs = {
            "poses": len(pose_rows) > 0,
            "gnss": len(gnss_rows) > 0,
        }
        missing_required_inputs = [name for name, present in required_inputs.items() if not present]

        return SessionPackageInterface(
            required_inputs=required_inputs,
            optional_inputs=optional_inputs,
            derived_outputs={
                "input_readiness.json": "必須入力、任意入力、診断進行可否の判定",
                "sensor_quality.json": "stream ごとの品質低下と警告理由",
                "frame_pose_index.csv": "frame と pose の対応表",
                "member_identity_map.json": "端末、主体、BT 識別子の対応表",
            },
            missing_required_inputs=missing_required_inputs,
            ready_for_diagnose=not missing_required_inputs,
        )

    def _range_from_rows(self, rows: list[dict[str, Any]], key: str) -> tuple[int, int] | None:
        if not rows:
            return None
        values = [int(float(row[key])) for row in rows if row.get(key) not in (None, "")]
        if not values:
            return None
        return min(values), max(values)

    def _range_from_row_aliases(self, rows: list[dict[str, Any]], *keys: str) -> tuple[int, int] | None:
        if not rows:
            return None
        values = [
            int(float(row[key]))
            for row in rows
            for key in keys
            if row.get(key) not in (None, "")
        ]
        if not values:
            return None
        return min(values), max(values)

    def _nearest_delta_ns(
        self,
        frame_rows: list[dict[str, Any]],
        sensor_rows: list[dict[str, Any]],
        sensor_keys: tuple[str, ...],
    ) -> int | None:
        if not frame_rows or not sensor_rows:
            return None
        sensor_values = sorted(
            int(float(row[key]))
            for row in sensor_rows
            for key in sensor_keys
            if row.get(key) not in (None, "")
        )
        if not sensor_values:
            return None

        nearest: int | None = None
        for row in frame_rows[: min(len(frame_rows), 60)]:
            frame_raw = row.get("elapsed_realtime_ns", row.get("timestamp_ns"))
            if frame_raw in (None, ""):
                continue
            frame_value = int(float(frame_raw))
            candidate = min(abs(frame_value - sensor_value) for sensor_value in sensor_values)
            nearest = candidate if nearest is None else min(nearest, candidate)
        return nearest
