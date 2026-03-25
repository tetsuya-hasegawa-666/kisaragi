# Python Session Parser

- `session_parser.py`: `iSensorium` session directory を読み込み、manifest / CSV / JSONL を統一的に扱う
- `validate_session.py`: 1 session を検証し、`MRL-3` 用の summary と join report を JSON 出力する

## 使用例

```powershell
python python/validate_session.py tmp/session-20260314-111930
```
