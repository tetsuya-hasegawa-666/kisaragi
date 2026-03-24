# agents.md

## --state の役割

- この階層は shared control file と project ごとの current state を保持する。

## shared と per-project の関係

- shared control file は `current_state.md` と `decision_log.md` を正本とする。
- shared control file は project 横断の承認待ち、共通 blocker、全体 next action を保持する。
- `prj-<project名>/current_state.md` は各 project の作業所有権、局所 blocker、局所 next action を保持する。
- project 固有の事項を shared control file にだけ残さない。
- project 横断の rule や判断を per-project file にだけ残さない。
