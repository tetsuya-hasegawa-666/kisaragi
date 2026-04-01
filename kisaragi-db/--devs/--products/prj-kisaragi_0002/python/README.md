# Python セッションパーサ

- `session_parser.py`: `trajectreview` session directory を読み込み、`SessionPackage` に必要な manifest / CSV / JSONL を統一的に扱う
- `validate_session.py`: 1 session を検証し、intake / diagnose 向け summary、join report、分担用 `SessionPackage` インターフェース出力を JSON 出力する
- `review_contracts.py`: 4 段階の handoff contract を code として保持し、文書と実装の整合確認に使う
- `modeling_colab_tool.py`: `DA3Metric-Large` 向けの Colab notebook 生成と remote result import を行う
- Python 実行時の bytecode cache は `--exsams/prj-kisaragi_0002/python-pycache/` を使うものとする

## 互換境界

- `iSensorium` 由来の `ble_scan.jsonl` と `frame_record.jsonl` を primary に読める
- `trajectreview` 用の `bt.jsonl` と `poses.jsonl` も読める
- legacy alias として `bt_events.csv` と `arcore_pose.csv` も読める
- `gnss` は optional input とする

## 分担用の追加出力

- `input_readiness.json` 相当: 必須入力、任意入力、診断進行可否
- `sensor_quality.json` 相当: sensor stream ごとの品質低下理由
- `sensor_quality.json` には `imuNearestDeltaNs`、`btNearestDeltaNs`、`poseNearestDeltaNs`、`completenessScore`、`poseCoverageRatio` を含める
- `frame_pose_index.csv` 相当: frame と pose の対応表
- `member_identity_map.json` 相当: 端末、主体、`BT` 識別子の対応表
- `session_package.json` 相当: 後段へ渡すための正規化済み `SessionPackage` 実体
- `space_handoff_manifest.json` 相当: `SpaceReconstruction` 着手可否、blocker、利用 artifact の要約
- `experiment_manifest.json` 相当: route ごとの frame sampling、intrinsics mode、depth projection、resource 制約
- `da3_input_manifest.json` 相当: `DA3Metric-Large` に渡す画像入力、`ARCore` pose、intrinsics 情報
- `depth_estimation_report.json` 相当: metric depth 推定の主要指標と failure reason
- `benchmark_summary.json` 相当: sampling / intrinsics route 比較結果
- `selected_route.json` 相当: 暫定採用 route と research route
- `colab_job_request.json` 相当: `Colab` notebook 実行契約

## 実行例

```powershell
$env:PYTHONPYCACHEPREFIX='C:\Users\tetsuya\kisaragi\kisaragi-db\--exsams\prj-kisaragi_0002\python-pycache'
python python/validate_session.py tmp/session-20260323-001
```

```powershell
python python/modeling_colab_tool.py build-notebook `
  --job-request tmp/session-20260323-001/trajectreview/modeling/colab_job_request.json `
  --selected-route tmp/session-20260323-001/trajectreview/modeling/selected_route.json `
  --output tmp/session-20260323-001/trajectreview/modeling/colab
```

- notebook の `CONFIG` は `session_root` を最小入力とし、`session_package.json`、`selected_route.json`、`colab_job_request.json` から `session_id`、`route_id`、`sampling profile`、`intrinsics mode` を自動で解決する。
- `input_root` は `session_root` の親 folder として扱い、`result_root` は結果保存先の親 folder とする。
