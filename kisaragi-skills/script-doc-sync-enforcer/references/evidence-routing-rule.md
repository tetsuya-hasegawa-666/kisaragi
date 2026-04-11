# evidence routing rule

## 目的

- test 結果や closeout 情報を、sharedlog ではなく既存の正しい記録先へ送るための rule とする。

## 基本方針

- 記録先は新設しない
- log のみで閉じない
- 既存の正本または既存の test summary へ送る

## routing

| 情報の種類 | 既定の記録先 |
| --- | --- |
| Codex 側 closeout、issue、resolution | `codex-mrl-test-evidence.md` |
| admin 実測、UX check 結果 | `admin-mrl-test-evidence.md` |
| test 実行要約、manifest | `--testlogs/` |
| admin 手順変更 | `admin-mrl-test-method.md` |

## 禁止

- sharedlog だけに結果を残して close する
- 新しい記録先を安易に増やす
- test 実行結果の所在が不明なまま close する
