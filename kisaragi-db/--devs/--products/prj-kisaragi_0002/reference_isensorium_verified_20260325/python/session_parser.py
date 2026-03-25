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
    recording_mode: str
    session_dir: Path
    stream_counts: dict[str, int]
    collector_status: dict[str, str]
    frame_time_range_ns: tuple[int, int] | None
    imu_time_range_ns: tuple[int, int] | None
    gnss_time_range_ns: tuple[int, int] | None
    ble_time_range_ns: tuple[int, int] | None
    arcore_time_range_ns: tuple[int, int] | None


class SessionParser:
    def __init__(self, session_dir: str | Path) -> None:
        self.session_dir = Path(session_dir)
        self.manifest_path = self.session_dir / "session_manifest.json"
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.timebase = self.manifest["timebase"]

    def load_summary(self) -> SessionSummary:
        frame_rows = self.load_csv("video_frame_timestamps.csv")
        imu_rows = self.load_csv("imu.csv")
        gnss_rows = self.load_csv("gnss.csv")
        ble_rows = self.load_jsonl("ble_scan.jsonl")
        arcore_rows = self.load_jsonl("arcore_pose.jsonl")

        return SessionSummary(
            session_id=self.manifest["sessionId"],
            status=self.manifest["status"],
            device_model=self.manifest["deviceModel"],
            recording_mode=self.manifest.get("recordingMode", self.manifest.get("recordingConfig", {}).get("recordingMode", "standard_handheld")),
            session_dir=self.session_dir,
            stream_counts={
                "frames": len(frame_rows),
                "imu": len(imu_rows),
                "gnss": len(gnss_rows),
                "ble": len(ble_rows),
                "arcore": len(arcore_rows),
            },
            collector_status=self.manifest.get("collectorStatus", {}),
            frame_time_range_ns=self._range_from_rows(frame_rows, "elapsed_realtime_ns"),
            imu_time_range_ns=self._range_from_rows(imu_rows, "elapsed_realtime_ns"),
            gnss_time_range_ns=self._range_from_rows(gnss_rows, "elapsed_realtime_ns"),
            ble_time_range_ns=self._range_from_rows(ble_rows, "elapsedRealtimeNanos"),
            arcore_time_range_ns=self._range_from_rows(arcore_rows, "elapsedRealtimeNanos"),
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

    def build_join_report(self) -> dict[str, Any]:
        frame_rows = self.load_csv("video_frame_timestamps.csv")
        imu_rows = self.load_csv("imu.csv")
        gnss_rows = self.load_csv("gnss.csv")
        ble_rows = self.load_jsonl("ble_scan.jsonl")
        arcore_rows = self.load_jsonl("arcore_pose.jsonl")

        return {
            "sessionId": self.manifest["sessionId"],
            "timebase": self.timebase,
            "frameCount": len(frame_rows),
            "imuNearestDeltaNs": self._nearest_delta_ns(frame_rows, imu_rows, "elapsed_realtime_ns"),
            "gnssNearestDeltaNs": self._nearest_delta_ns(frame_rows, gnss_rows, "elapsed_realtime_ns"),
            "bleNearestDeltaNs": self._nearest_delta_ns(frame_rows, ble_rows, "elapsedRealtimeNanos"),
            "arcoreNearestDeltaNs": self._nearest_delta_ns(frame_rows, arcore_rows, "elapsedRealtimeNanos"),
            "metadataSufficiency": {
                "hasMonotonicSessionBase": "sessionStartElapsedRealtimeNanos" in self.timebase,
                "hasWallClockBase": "sessionStartWallTimeMs" in self.timebase,
                "hasVideoFrameTimeline": len(frame_rows) > 0,
                "hasImuTimeline": len(imu_rows) > 0,
                "hasGnssTimeline": len(gnss_rows) > 0,
                "hasBleTimeline": len(ble_rows) > 0,
                "hasArCoreTimeline": len(arcore_rows) > 0,
                "hasCollectorStatus": bool(self.manifest.get("collectorStatus")),
            },
        }

    def _range_from_rows(self, rows: list[dict[str, Any]], key: str) -> tuple[int, int] | None:
        if not rows:
            return None
        values = [int(float(row[key])) for row in rows if row.get(key) not in (None, "")]
        if not values:
            return None
        return min(values), max(values)

    def _nearest_delta_ns(
        self,
        frame_rows: list[dict[str, Any]],
        sensor_rows: list[dict[str, Any]],
        sensor_key: str,
    ) -> int | None:
        if not frame_rows or not sensor_rows:
            return None
        sensor_values = sorted(
            int(float(row[sensor_key]))
            for row in sensor_rows
            if row.get(sensor_key) not in (None, "")
        )
        if not sensor_values:
            return None

        nearest: int | None = None
        for row in frame_rows[: min(len(frame_rows), 60)]:
            frame_value = int(float(row["elapsed_realtime_ns"]))
            candidate = min(abs(frame_value - sensor_value) for sensor_value in sensor_values)
            nearest = candidate if nearest is None else min(nearest, candidate)
        return nearest
