# mrl-ux-valid

## 目的

この文書は `prj-kisaragi_0002` の `MRL` / `mRL` が `pass` になった根拠を、UX と実行証跡の両面から集約する。

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
  - raw build cache、binary results、pycache は `kisaragi-db/--exsams/prj-kisaragi_0002/` に出力する
  - 要約 report と summary は `kisaragi-db/--devs/--testlogs/prj-kisaragi_0002/` に出力する
- 主要 evidence:
  - `kisaragi-db/--devs/--plans/prj-kisaragi_0002/b2t-plans-result.md`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/scripts/run_python_tests.ps1`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/scripts/run_android_unit_tests.ps1`

## 残作業

- 現行 `MRL` 計画は close した。
- 次段では、pass 済み contract を実データ pipeline と viewer の実利用へ拡張する。

## 2026-03-25 latest exsams output recheck

- 対象:
  - `run_python_tests.ps1`
  - `run_android_unit_tests.ps1`
- 結果:
  - Python unittest: pass
  - Android unit test: pass
- 最新 raw output 確認:
  - Python: `--exsams/prj-kisaragi_0002/python-pycache/.../test_project_contracts.cpython-314.pyc` と `test_session_parser.cpython-314.pyc` が `2026-03-25 19:12:07` に更新された
  - Android: `--exsams/prj-kisaragi_0002/gradle-user-home/daemon/8.10.2/registry.bin.lock` などの Gradle raw artifact が `2026-03-25 19:12:08` に更新された
- 判定: `prj-kisaragi_0002` は、最も最近実施した test の raw data を `--exsams` 側へ出力できる

## 2026-03-25 `MRL-5` closeout

- 対象 gate:
  - `MRL-5`
  - `mRL-5.1` から `mRL-5.3`
- UX 観点:
  - app 起動直後に `iSensorium セッションを選択` が `Next Action` として見える
  - `Extraction` card で抽出元、抽出先、`ready_for_diagnose`、欠落入力、quality 数値を 1 画面で読める
  - `ux_check_manual.md` を、抽出 UI を含む最小操作手順へ更新した
- 実装 / test 観点:
  - Python unittest: `test_session_parser.py`
  - Android unit test: `ReviewScreenControllerTest.kt`、`ISensoriumExtractionServiceTest.kt`
  - script 実行:
    - `run_python_tests.ps1`
    - `run_android_unit_tests.ps1`
  - device install:
    - `gradlew.bat installDebug`
- 抽出 bundle 観点:
  - raw file は `session_id/isensorium/`
  - 派生 file は `session_id/trajectreview/`
  - `sensor_quality.json` に時刻整列 delta、completeness score、pose coverage ratio が入る
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/ISensoriumExtractionService.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py`
  - `kisaragi-db/--devs/--testlogs/prj-kisaragi_0002/reports/python-unittest-summary.md`
  - `kisaragi-db/--devs/--testlogs/prj-kisaragi_0002/reports/android-test-summary.md`

## 2026-03-25 `MRL-6` closeout

- 対象 gate:
  - `MRL-6`
  - `mRL-6.1` から `mRL-6.3`
- UX 観点:
  - 抽出結果画面で `ready_for_space_reconstruction` と blocker を確認できる
  - raw bundle に主カメラ動画を保持したまま、後段着手判断を 1 画面で行える
- 実装 / test 観点:
  - Python unittest: `test_session_parser.py`、`test_project_contracts.py`
  - Android unit test: `ISensoriumExtractionServiceTest.kt`
  - device install:
    - `gradlew.bat installDebug`
- handoff artifact 観点:
  - `session_package.json` が timebase、source file、stream count、quality 指標、required / optional input を保持する
  - `space_handoff_manifest.json` が `ready_for_space_reconstruction`、blocker、consumed artifact、next action を保持する
  - `video.mp4` と `video_events.jsonl` を raw bundle に保持する
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/ISensoriumExtractionService.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/python/session_parser.py`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py`
