# reviework 実装物 README

この directory は `reviework` の source-of-truth 実装物だけを置く。

## 配置規則

- `app/`、`python/`、`gradle/`、`build.gradle.kts` などの実装 source はここに置く
- `app/build/`、`.gradle/`、`.kotlin/`、`__pycache__/` のような生成物はここに置かない
- Android build output と Gradle cache は `--trial-data/prj-reviework/` に出す
- unit test の XML / HTML / binary result は `--process/--testlogs/prj-reviework/` に出す
- Python bytecode cache は `--trial-data/prj-reviework/python-pycache/` に出す

## 実行入口

- Android unit test:

```powershell
pwsh -File .\scripts\run_android_unit_tests.ps1
```

- Python unit test:

```powershell
pwsh -File .\scripts\run_python_tests.ps1
```
