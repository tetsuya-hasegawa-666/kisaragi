# trajectreview 実装物 README

この directory は `trajectreview` の source-of-truth 実装物だけを置く。

## 配置規則

- `app/`、`python/`、`gradle/`、`build.gradle.kts` などの実装 source はここに置く
- `app/build/`、`.gradle/`、`.kotlin/`、`__pycache__/` のような生成物はここに置かない
- Android build output、Gradle cache、unit test の raw result は `kisaragi-db/--exsams/prj-kisaragi_0002/` に出す
- unit test の summary は `kisaragi-db/--devs/--testlogs/prj-kisaragi_0002/` に出す
- Python bytecode cache は `kisaragi-db/--exsams/prj-kisaragi_0002/python-pycache/` に出す

## 実行入口

- Android app:
  - `trajectreview` は `iSensorium` session folder を選択し、`session_id/isensorium/` と `session_id/trajectreview/` を app の external files 配下へ抽出する
  - `Extraction` card に、抽出元、抽出先、`ready_for_diagnose`、`ready_for_space_reconstruction`、欠落入力、quality 数値を表示する
  - 抽出後は `session_package.json` と `space_handoff_manifest.json` を生成し、後段の `SpaceReconstruction` 着手単位へつなぐ

- Android unit test:

```powershell
pwsh -File .\scripts\run_android_unit_tests.ps1
```

- Python unit test:

```powershell
pwsh -File .\scripts\run_python_tests.ps1
```

## 揮発 runtime runbook

- `Colab`、remote notebook、揮発 container の bootstrap 手順は、shared worklog ではなく product 側の runbook に昇格して保持する。
- `prj-kisaragi_0002` の `DA3 sequence-anchor` `Colab bootstrap` 正本は [colab/da3_ngl_increpose_RB.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab\da3_ngl_increpose_RB.md) とする。
- admin が Colab でそのまま実行する notebook companion は [colab/da3_ngl_increpose_RB.ipynb](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab\da3_ngl_increpose_RB.ipynb) とする。
- `Colab` で実行する notebook と runbook は [colab](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab) を canonical source とし、[modeling/evidence](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\evidence) には新規 script を保存しない。
- runbook は `candidate` と `adopted` を分け、admin 実測で end-to-end が通った手順だけを `truly pass` として昇格する。
