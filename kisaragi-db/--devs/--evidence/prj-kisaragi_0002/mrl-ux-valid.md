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
  - app 起動直後に `入力セッションを選択` が `Next Action` として見える
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
- 
## 2026-03-26 `MRL-7` closeout

- 対象 gate:
  - `MRL-7`
  - `mRL-7.1` から `mRL-7.3`
- UX 観点:
  - `trajectreview-correcting`、`trajectreview-modeling`、`trajectreview-reviewing`、統合 app がそれぞれ自分の役割だけを主表示にする
  - 統合 app は `correcting / modeling / reviewing` を 1 画面で俯瞰できる
- 実装 / test 観点:
  - Android unit test: `ReviewScreenControllerTest.kt`
  - build:
    - `:app:testDebugUnitTest`
    - `:correcting:assembleDebug`
    - `:modeling:assembleDebug`
    - `:reviewing:assembleDebug`
  - device install:
    - `:app:installDebug`
    - `:correcting:installDebug`
    - `:modeling:installDebug`
    - `:reviewing:installDebug`
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/settings.gradle.kts`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/AppWorkflowProfile.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`

## 2026-03-26 `MRL-8` closeout

- 対象 gate:
  - `MRL-8`
  - `mRL-8.1` から `mRL-8.3`
- UX 観点:
  - `correcting` と統合 app は抽出した実 bundle を再読込して実データ状態を表示する
  - `modeling` は `Colab` account 未取得でも local sample model と `colab_job_request.json` を生成する
  - `reviewing` と統合 app は `local_model_summary.json` と `review_artifact_stub.json` を読んで verify / review 状態を組み立てる
- 実装 / test 観点:
  - Android unit test:
    - `WorkflowBundleServiceTest.kt`
    - `LocalModelingServiceTest.kt`
    - `ReviewScreenControllerTest.kt`
  - build / install:
    - `:app:testDebugUnitTest`
    - `:correcting:assembleDebug`
    - `:modeling:assembleDebug`
    - `:reviewing:assembleDebug`
    - `:app:installDebug`
    - `:correcting:installDebug`
    - `:modeling:installDebug`
    - `:reviewing:installDebug`
- 生成 artifact 観点:
  - `local_model_summary.json`
  - `colab_job_request.json`
  - `review_artifact_stub.json`
  - `modeling_handoff_manifest.json`
- 主要 evidence:
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/WorkflowBundleService.kt`
  - `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/WorkflowBundleServiceTest.kt`
  - `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/LocalModelingServiceTest.kt`
