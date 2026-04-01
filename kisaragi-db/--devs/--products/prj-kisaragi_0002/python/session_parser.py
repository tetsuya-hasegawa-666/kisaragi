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
                    rows.append(self._flatten_json(json.loads(line)))
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

    def _first_existing_name(self, *filenames: str) -> str | None:
        path = self._find_first_existing(*filenames)
        return path.name if path is not None else None

    def load_frame_rows(self) -> list[dict[str, Any]]:
        return self.load_csv_aliases("video_frame_timestamps.csv", "frames.csv")

    def load_bt_rows(self) -> list[dict[str, Any]]:
        rows = self.load_jsonl_aliases("bt.jsonl", "ble_scan.jsonl")
        if rows:
            return rows
        return self.load_csv_aliases("bt_events.csv", "bt.csv")

    def load_pose_rows(self) -> list[dict[str, Any]]:
        rows = self.load_jsonl_aliases("frame_record.jsonl", "poses.jsonl", "arcore_pose.jsonl")
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
        has_frame_records = any(row.get("imageFileName") for row in pose_rows)
        video_present = (self.session_dir / "video.mp4").exists()
        video_events_present = (self.session_dir / "video_events.jsonl").exists()

        required_inputs = {
            "session_manifest": self.manifest_path is not None and self.manifest_path.exists(),
            "video": video_present,
            "frames": has_frame_records or len(frame_rows) > 0,
            "imu": len(imu_rows) > 0,
            "bt": len(bt_rows) > 0,
        }
        optional_inputs = {
            "poses": len(pose_rows) > 0,
            "gnss": len(gnss_rows) > 0,
            "video_events": video_events_present,
        }
        missing_required_inputs = [name for name, present in required_inputs.items() if not present]

        return SessionPackageInterface(
            required_inputs=required_inputs,
            optional_inputs=optional_inputs,
            derived_outputs={
                "input_readiness.json": "必須入力、任意入力、診断進行可否の判定",
                "sensor_quality.json": "stream ごとの品質低下と警告理由",
                "frame_pose_index.csv": "frame と pose の対応表",
                "camera_calibration_summary.json": "frame timestamp、camera intrinsics、lens distortion の要約",
                "member_identity_map.json": "端末、主体、BT 識別子の対応表",
                "session_package.json": "後段へ渡すための正規化済み SessionPackage 実体",
                "space_handoff_manifest.json": "SpaceReconstruction 着手可否と blocker の要約",
            },
            missing_required_inputs=missing_required_inputs,
            ready_for_diagnose=not missing_required_inputs,
        )

    def build_session_package_payload(self) -> dict[str, Any]:
        summary = self.load_summary()
        join_report = self.build_join_report()
        package_interface = self.build_session_package_interface()
        calibration = self._camera_calibration_summary(self.load_pose_rows())
        recording_config = self.manifest.get("recordingConfig", {})
        arcore_enabled = bool(recording_config.get("arCoreEnabled", self.manifest.get("arCoreEnabled", True)))
        arcore_interval_ms = int(recording_config.get("arCoreIntervalMs", self.manifest.get("arCoreIntervalMs", 33)))
        frame_record_every_n_updates = int(recording_config.get("frameRecordEveryNUpdates", self.manifest.get("frameRecordEveryNUpdates", 1)))
        image_directory = "images" if (self.session_dir / "images").exists() else "trajectreview/images"

        return {
            "sessionId": summary.session_id,
            "status": summary.status,
            "deviceModel": summary.device_model,
            "sessionMode": summary.session_mode,
            "sessionDir": str(self.session_dir),
            "timebase": self.timebase,
            "requiredInputs": package_interface.required_inputs,
            "optionalInputs": package_interface.optional_inputs,
            "streamCounts": summary.stream_counts,
            "collectorStatus": summary.collector_status,
            "scores": {
                "completenessScore": self._completeness_score(package_interface.required_inputs),
                "poseCoverageRatio": self._pose_coverage_ratio(
                    frame_rows=self.load_frame_rows(),
                    pose_rows=self.load_pose_rows(),
                    arcore_enabled=arcore_enabled,
                    arcore_interval_ms=arcore_interval_ms * max(frame_record_every_n_updates, 1),
                ),
                "imageIntrinsicsCoverageRatio": calibration["imageIntrinsicsCoverageRatio"],
                "lensDistortionCoverageRatio": calibration["lensDistortionCoverageRatio"],
            },
            "cameraCalibration": calibration,
            "nearestDeltaNs": {
                "imuNearestDeltaNs": join_report["imuNearestDeltaNs"],
                "gnssNearestDeltaNs": join_report["gnssNearestDeltaNs"],
                "btNearestDeltaNs": join_report["btNearestDeltaNs"],
                "poseNearestDeltaNs": join_report["poseNearestDeltaNs"],
            },
            "mainVideoPath": "video.mp4",
            "imageDirectory": image_directory,
            "framePoseIndexPath": "trajectreview/frame_pose_index.csv",
            "cameraCalibrationSummaryPath": "trajectreview/camera_calibration_summary.json",
            "frameRecordPath": self._first_existing_name("frame_record.jsonl", "poses.jsonl", "arcore_pose.jsonl", "arcore_pose.csv"),
            "arcorePosePath": self._first_existing_name("frame_record.jsonl", "poses.jsonl", "arcore_pose.jsonl", "arcore_pose.csv"),
            "sourceFiles": {
                "manifest": self.manifest_path.name if self.manifest_path is not None else None,
                "video": "video.mp4" if (self.session_dir / "video.mp4").exists() else None,
                "frames": self._first_existing_name("video_frame_timestamps.csv", "frames.csv"),
                "imu": "imu.csv" if (self.session_dir / "imu.csv").exists() else None,
                "gnss": "gnss.csv" if (self.session_dir / "gnss.csv").exists() else None,
                "bt": self._first_existing_name("bt.jsonl", "ble_scan.jsonl", "bt_events.csv", "bt.csv"),
                "frameRecord": self._first_existing_name("frame_record.jsonl", "poses.jsonl", "arcore_pose.jsonl", "arcore_pose.csv"),
                "poses": self._first_existing_name("frame_record.jsonl", "poses.jsonl", "arcore_pose.jsonl", "arcore_pose.csv"),
                "videoEvents": "video_events.jsonl" if (self.session_dir / "video_events.jsonl").exists() else None,
                "cameraCalibrationSummary": "camera_calibration_summary.json",
            },
        }

    def build_space_handoff_manifest(self) -> dict[str, Any]:
        package = self.build_session_package_payload()
        metadata = self.build_join_report()["metadataSufficiency"]
        blockers: list[str] = []

        if not package["requiredInputs"]["video"]:
            blockers.append("video.mp4 が不足している")
        if not package["requiredInputs"]["frames"]:
            blockers.append("frame timeline が不足している")
        if not package["requiredInputs"]["imu"]:
            blockers.append("imu.csv が不足している")
        if not metadata["hasMonotonicSessionBase"]:
            blockers.append("sessionStartElapsedRealtimeNanos が不足している")
        if not self.load_pose_rows():
            blockers.append("frame_record.jsonl が不足している")

        return {
            "sessionId": package["sessionId"],
            "targetStage": "SpaceReconstruction",
            "readyForSpaceReconstruction": not blockers,
            "blockers": blockers,
            "warnings": package["cameraCalibration"].get("warnings", []),
            "requiredArtifacts": [
                "session_package.json",
                "input_readiness.json",
                "sensor_quality.json",
                "frame_pose_index.csv",
                "camera_calibration_summary.json",
                "frame_record.jsonl",
                "images",
            ],
            "availableSourceFiles": package["sourceFiles"],
            "recommendedNextAction": "空間再構成を開始" if not blockers else "入力条件を見直す",
            "allowModelingProceed": True,
        }

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

    def _completeness_score(self, required_inputs: dict[str, bool]) -> float:
        return sum(1 for present in required_inputs.values() if present) / len(required_inputs) if required_inputs else 0.0

    def _pose_coverage_ratio(
        self,
        frame_rows: list[dict[str, Any]],
        pose_rows: list[dict[str, Any]],
        arcore_enabled: bool,
        arcore_interval_ms: int,
    ) -> float:
        if not arcore_enabled:
            return 1.0
        if not pose_rows:
            return 0.0
        frame_times = [
            int(float(row.get("elapsed_realtime_ns", row.get("timestamp_ns"))))
            for row in frame_rows
            if row.get("elapsed_realtime_ns", row.get("timestamp_ns")) not in (None, "")
        ]
        duration_ns = max(frame_times) - min(frame_times) if len(frame_times) >= 2 else 0
        interval_ns = max(1, arcore_interval_ms) * 1_000_000
        expected_pose_samples = max(1, duration_ns // interval_ns + 1)
        return min(1.0, len(pose_rows) / expected_pose_samples)

    def _camera_calibration_summary(self, pose_rows: list[dict[str, Any]]) -> dict[str, Any]:
        calibration_frame_count = sum(
            1 for row in pose_rows if self._row_has_any_value(row, "frameTimestampNs", "captureTimestampNs", "timestamp_ns")
        )
        valid_pose_count = sum(
            1 for row in pose_rows if self._row_has_any_value(row, "pose.tx", "translation")
        )
        image_intrinsics_count = sum(
            1 for row in pose_rows if self._row_has_any_value(row, "imageIntrinsics.fx", "imageFocalLength", "imagePrincipalPoint", "imageDimensions")
        )
        texture_intrinsics_count = sum(
            1 for row in pose_rows if self._row_has_any_value(row, "textureIntrinsics.fx", "textureFocalLength", "texturePrincipalPoint", "textureDimensions")
        )
        lens_distortion_count = sum(
            1 for row in pose_rows if self._row_has_any_value(row, "lensDistortion.coefficients", "lensDistortion")
        )
        image_intrinsics_attempt_count = sum(
            1 for row in pose_rows if str(row.get("captureDiagnostics.imageIntrinsics.requested", "")).lower() == "true"
        )
        image_intrinsics_success_count = sum(
            1 for row in pose_rows if str(row.get("captureDiagnostics.imageIntrinsics.succeeded", "")).lower() == "true"
        )
        texture_intrinsics_attempt_count = sum(
            1 for row in pose_rows if str(row.get("captureDiagnostics.textureIntrinsics.requested", "")).lower() == "true"
        )
        texture_intrinsics_success_count = sum(
            1 for row in pose_rows if str(row.get("captureDiagnostics.textureIntrinsics.succeeded", "")).lower() == "true"
        )
        lens_distortion_attempt_count = sum(
            1 for row in pose_rows if str(row.get("captureDiagnostics.lensDistortion.requested", "")).lower() == "true"
        )
        lens_distortion_success_count = sum(
            1 for row in pose_rows if str(row.get("captureDiagnostics.lensDistortion.succeeded", "")).lower() == "true"
        )
        has_capture_diagnostics = any(
            count > 0
            for count in (
                image_intrinsics_attempt_count,
                texture_intrinsics_attempt_count,
                lens_distortion_attempt_count,
            )
        )
        total_pose_rows = len(pose_rows)
        image_coverage = 0.0 if total_pose_rows == 0 else min(1.0, image_intrinsics_count / total_pose_rows)
        texture_coverage = 0.0 if total_pose_rows == 0 else min(1.0, texture_intrinsics_count / total_pose_rows)
        distortion_coverage = 0.0 if total_pose_rows == 0 else min(1.0, lens_distortion_count / total_pose_rows)
        timestamps = [
            int(float(row[key]))
            for row in pose_rows
            for key in ("frameTimestampNs", "captureTimestampNs", "timestamp_ns")
            if row.get(key) not in (None, "", "null", "None")
        ]
        warnings: list[str] = []
        if image_coverage < 1.0:
            warnings.append("imageIntrinsicsCoverageRatio が 1.0 未満")
        if distortion_coverage < 1.0:
            warnings.append("lensDistortionCoverageRatio が 1.0 未満")
        if image_intrinsics_attempt_count > 0 and image_intrinsics_success_count == 0:
            warnings.append("imageIntrinsics の読取試行はあるが成功 0 件")
        signatures = {
            "|".join(
                [
                    str(row.get("imageIntrinsics.fx", row.get("imageFocalLength", ""))),
                    str(row.get("imageIntrinsics.fy", "")),
                    str(row.get("imageIntrinsics.cx", row.get("imagePrincipalPoint", ""))),
                    str(row.get("imageIntrinsics.cy", "")),
                    str(row.get("imageIntrinsics.width", row.get("imageDimensions", ""))),
                    str(row.get("imageIntrinsics.height", "")),
                ]
            )
            for row in pose_rows
            if self._row_has_any_value(row, "imageIntrinsics.fx", "imageFocalLength")
        }
        intrinsics_mode = "unknown"
        if image_intrinsics_count > 0:
            intrinsics_mode = "per_frame" if len(signatures) > 1 else "session_fixed"
        possible_pre_calibration_implementation_data = (
            total_pose_rows > 0
            and image_intrinsics_count == 0
            and texture_intrinsics_count == 0
            and lens_distortion_count == 0
            and not has_capture_diagnostics
        )
        blockers: list[str] = []
        if valid_pose_count == 0:
            blockers.append("pose がほぼ 0 件")
        if image_intrinsics_count == 0:
            blockers.append("intrinsics がほぼ 0 件")
        if possible_pre_calibration_implementation_data:
            warnings.append("この session は calibration export 実装前に取得された可能性があります")
        return {
            "specVersion": "2026-03-27-calibration-export-v1",
            "recordCount": total_pose_rows,
            "validPoseCount": valid_pose_count,
            "calibrationFrameCount": calibration_frame_count,
            "imageIntrinsicsCount": image_intrinsics_count,
            "textureIntrinsicsCount": texture_intrinsics_count,
            "lensDistortionCount": lens_distortion_count,
            "imageIntrinsicsCoverageRatio": image_coverage,
            "textureIntrinsicsCoverageRatio": texture_coverage,
            "lensDistortionCoverageRatio": distortion_coverage,
            "timestampStartNs": min(timestamps) if timestamps else None,
            "timestampEndNs": max(timestamps) if timestamps else None,
            "intrinsicsModeCandidate": intrinsics_mode,
            "intrinsicsChangedDuringRecording": intrinsics_mode == "per_frame",
            "possiblePreCalibrationImplementationData": possible_pre_calibration_implementation_data,
            "captureDiagnostics": {
                "imageIntrinsicsAttemptCount": image_intrinsics_attempt_count,
                "imageIntrinsicsSuccessCount": image_intrinsics_success_count,
                "textureIntrinsicsAttemptCount": texture_intrinsics_attempt_count,
                "textureIntrinsicsSuccessCount": texture_intrinsics_success_count,
                "lensDistortionAttemptCount": lens_distortion_attempt_count,
                "lensDistortionSuccessCount": lens_distortion_success_count,
            },
            "recommendedModelingRoutes": [
                "route-da3metric-large-5fps-static-intrinsics",
                "route-da3metric-large-10fps-static-intrinsics",
                "route-da3metric-large-10fps-per-frame-intrinsics",
            ],
            "warnings": warnings,
            "blockers": blockers,
        }

    def _row_has_any_value(self, row: dict[str, Any], *keys: str) -> bool:
        return any(row.get(key) not in (None, "", "null", "None") for key in keys)

    def _flatten_json(self, value: Any, prefix: str = "") -> dict[str, Any]:
        if isinstance(value, dict):
            flattened: dict[str, Any] = {}
            for key, item in value.items():
                next_prefix = f"{prefix}.{key}" if prefix else key
                flattened.update(self._flatten_json(item, next_prefix))
                if prefix == "":
                    flattened[key] = item if not isinstance(item, (dict, list)) else json.dumps(item)
            return flattened
        if isinstance(value, list):
            return {prefix: json.dumps(value)}
        return {prefix: value}
