# Python セッションパーサ

- `session_parser.py`: `reviework` session directory を読み込み、`SessionPackage` に必要な manifest / CSV / JSONL を統一的に扱う
- `validate_session.py`: 1 session を検証し、intake / diagnose 向け summary、join report、分担用 `SessionPackage` インターフェース出力を JSON 出力する
- `review_contracts.py`: 4 段階の handoff contract を code として保持し、文書と実装の整合確認に使う
- Python 実行時の bytecode cache は `--exsams/prj-kisaragi_0002/python-pycache/` を使うものとする

## 互換境界

- `iSensorium` 由来の `ble_scan.jsonl` と `arcore_pose.jsonl` を読める
- `reviework` 用の `bt.jsonl` と `poses.jsonl` も読める
- `gnss` は optional input とする

## 分担用の追加出力

- `input_readiness.json` 相当: 必須入力、任意入力、診断進行可否
- `sensor_quality.json` 相当: sensor stream ごとの品質低下理由
- `frame_pose_index.csv` 相当: frame と pose の対応表
- `member_identity_map.json` 相当: 端末、主体、`BT` 識別子の対応表

## 実行例

```powershell
$env:PYTHONPYCACHEPREFIX='C:\Users\tetsuya\kisaragi\kisaragi-db\--exsams\prj-kisaragi_0002\python-pycache'
python python/validate_session.py tmp/session-20260323-001
```
