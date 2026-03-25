from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class StageHandoffContract:
    stage_id: str
    stage_name: str
    owned_by: str
    input_contracts: list[str]
    output_contracts: list[str]
    handoff_conditions: list[str]


def build_stage_handoff_contracts() -> list[StageHandoffContract]:
    return [
        StageHandoffContract(
            stage_id="stage-1",
            stage_name="InputPackaging",
            owned_by="入力受理と時刻整列",
            input_contracts=[
                "session_manifest.json",
                "video_frame_timestamps.csv",
                "imu.csv",
                "bt.jsonl or ble_scan.jsonl",
                "poses.jsonl or arcore_pose.jsonl",
                "gnss.csv",
            ],
            output_contracts=[
                "SessionPackage",
                "input_readiness.json",
                "sensor_quality.json",
                "frame_pose_index.csv",
                "member_identity_map.json",
            ],
            handoff_conditions=[
                "主カメラ動画、主カメラ IMU、人物側 IMU の充足が判定済みである",
                "主体、端末、時刻基準の対応が追える",
                "iSensorium 生出力と reviework 派生出力が分離されている",
            ],
        ),
        StageHandoffContract(
            stage_id="stage-2",
            stage_name="SpaceReconstruction",
            owned_by="主空間再構成",
            input_contracts=[
                "SessionPackage",
                "input_readiness.json",
                "sensor_quality.json",
                "frame_pose_index.csv",
            ],
            output_contracts=[
                "SpacePackage",
                "space_quality.json",
                "coverage_report.json",
                "main_camera_path.csv",
            ],
            handoff_conditions=[
                "主空間基準が一意に決まっている",
                "COLMAP から 3DGS へ進める可否が判定済みである",
            ],
        ),
        StageHandoffContract(
            stage_id="stage-3",
            stage_name="TrajectoryReconstruction",
            owned_by="人物経路再構成",
            input_contracts=[
                "SessionPackage",
                "SpacePackage",
                "member_identity_map.json",
                "main_camera_path.csv",
                "space_quality.json",
            ],
            output_contracts=[
                "TrajectoryPackage",
                "trajectory_quality.json",
                "relink_events.json",
                "attention_seed.json",
            ],
            handoff_conditions=[
                "主カメラ path と人物 path が主空間座標系に載っている",
                "不確実区間と再拘束点が識別できる",
            ],
        ),
        StageHandoffContract(
            stage_id="stage-4",
            stage_name="AssemblyAndViewer",
            owned_by="閲覧成果物組立と viewer 表示",
            input_contracts=[
                "SpacePackage",
                "TrajectoryPackage",
                "space_quality.json",
                "trajectory_quality.json",
                "attention_seed.json",
            ],
            output_contracts=[
                "ReviewArtifact",
                "viewer_manifest.json",
                "timeline.json",
                "attention_points.json",
                "same_time_highlights.json",
            ],
            handoff_conditions=[
                "閲覧時に必要な quality、attention point、同時刻ハイライトが欠落なく束ねられている",
                "Viewer は read-only で扱える",
            ],
        ),
    ]


def build_stage_handoff_manifest() -> list[dict[str, object]]:
    return [asdict(contract) for contract in build_stage_handoff_contracts()]
