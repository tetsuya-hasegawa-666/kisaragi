# mrl-ux-valid

## 目的

この文書は `prj-reviework` の `MRL` / `mRL` が `pass` になった根拠を、UX と実行証跡の両面から集約する。

## 2026-03-25 closeout

- 対象 gate:
  - `MRL-1` から `MRL-4`
  - `mRL-1.1` から `mRL-4.3`
- UX 観点:
  - `Next Action + Thin Status` で diagnose、run、verify、review を段階別に読める
  - 同時刻ハイライト、`attention point`、不確実区間、成果物境界を UI 契約として保持できる
  - 4 分担の handoff contract を code と文書の両方で読める
- 実装 / test 観点:
  - Python unittest: `test_session_parser.py`、`test_project_contracts.py`
  - Android unit test: `ReviewScreenControllerTest.kt`
  - script 実行:
    - `run_python_tests.ps1`
    - `run_android_unit_tests.ps1`
- routing 観点:
  - raw build cache、binary results、pycache は `kisaragi-db/--exsams/prj-reviework/` に出力する
  - 要約 report と summary は `kisaragi-db/--devs/--testlogs/prj-reviework/` に出力する
- 主要 evidence:
  - `kisaragi-db/--devs/--plans/prj-reviework/b2t-plans-result.md`
  - `kisaragi-db/--devs/--testcode/prj-reviework/test_session_parser.py`
  - `kisaragi-db/--devs/--testcode/prj-reviework/test_project_contracts.py`
  - `kisaragi-db/--devs/--testcode/prj-reviework/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
  - `kisaragi-db/--devs/--products/prj-reviework/scripts/run_python_tests.ps1`
  - `kisaragi-db/--devs/--products/prj-reviework/scripts/run_android_unit_tests.ps1`

## 残作業

- 現行 `MRL` 計画は close した。
- 次段では、pass 済み contract を実データ pipeline と viewer の実利用へ拡張する。
