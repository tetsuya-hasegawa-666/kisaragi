# isensorium verified reference snapshot

この文書は `prj-kisaragi_0002` が参照用に保持する `iSensorium` verified snapshot の確認結果を記録する正本とする。

## snapshot

- source origin: `C:\Users\tetsuya\sandbox\codev-db\--process\--products\prj-isensorium`
- source revision: `45e5517`
- mirrored product path: `C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\reference_isensorium_verified_20260325`
- mirrored test path: `C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--testcode\prj-kisaragi_0002\reference_isensorium_verified_20260325`

## mirror scope

- `app/`
- `python/`
- `scripts/`
- `gradle/`
- `data/`
- `build.gradle.kts`
- `gradle.properties`
- `gradlew`
- `gradlew.bat`
- `settings.gradle.kts`
- `android-test/`
- `test_session_parser.py`

## mirror 補足

- `kisaragi` 内で自己完結して test できるよう、mirror 側 `app/build.gradle.kts` の `sourceSets.test` は mirror 済み testcode path を参照する
- `kisaragi` 内で自己完結して Python test できるよう、mirror 側 `test_session_parser.py` は mirror 済み `python/session_parser.py` を参照する
- source logic の本体は mirror 作成時点の `iSensorium` product code を維持する
- 2026-03-25 時点で mirror app は比較用 install のため `applicationId = com.kisaragi.isensorium`、表示名 `kisaragi-iSensorium` とする

## verification

- verification date: `2026-03-25`
- device: `Xperia 5 III` `SO-53B`
- commands:
  - source 側 `gradlew.bat test --console=plain`: pass
  - source 側 `python test_session_parser.py`: pass
  - source 側 `gradlew.bat installDebug --console=plain`: pass
  - source 側 `scripts/run_short_session_harness.ps1 -Runs 1 -RecordSeconds 2`: pass
  - mirror 側 `gradlew.bat test --console=plain`: pass
  - mirror 側 `python test_session_parser.py`: pass
  - mirror 側 `gradlew.bat installDebug --console=plain`: pass
  - mirror 側 `scripts/run_short_session_harness.ps1 -Runs 1 -RecordSeconds 2`: pass
  - comparison app install check `adb shell pm list packages | findstr kisaragi.isensorium`: pass
  - comparison app activity resolve `adb shell cmd package resolve-activity --brief com.kisaragi.isensorium`: pass

## latest observed runtime result

- latest observed session id from mirror harness: `session-20260325-204738`
- harness output は recent session list に新しい session id が追加される形で確認した
- install は `SO-53B - 13` に対して成功した
- installed package は `com.kisaragi.isensorium`
- launcher activity は `com.kisaragi.isensorium/com.isensorium.app.MainActivity`

## judgement

- `prj-kisaragi_0002` は `iSensorium` 本体一式を、source 実装詳細の参照用かつ再検証可能な mirror として `kisaragi` 内に保持した
- `project-truth` は truth と pointer を保持し、mirror 実体は `--products` と `--testcode` へ分離した
- 以後 `trajectreview` の intake、抽出、時刻整列、collector 起動順の確認はこの mirror を基準に追跡できる
