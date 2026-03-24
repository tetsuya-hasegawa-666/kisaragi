# Python セッションパーサ

- `session_parser.py`: `reviework` session directory を読み込み、`SessionPackage` に必要な manifest / CSV / JSONL を統一的に扱う
- `validate_session.py`: 1 session を検証し、intake / diagnose 向け summary と join report を JSON 出力する
- Python 実行時の bytecode cache は `--trial-data/prj-reviework/python-pycache/` を使うものとする

## 互換境界

- `iSensorium` 由来の `ble_scan.jsonl` と `arcore_pose.jsonl` を読める
- `reviework` 用の `bt.jsonl` と `poses.jsonl` も読める
- `gnss` は optional input とする

## 実行例

```powershell
$env:PYTHONPYCACHEPREFIX='C:\Users\tetsuya\sandbox\codev-db\--trial-data\prj-reviework\python-pycache'
python python/validate_session.py tmp/session-20260323-001
```
