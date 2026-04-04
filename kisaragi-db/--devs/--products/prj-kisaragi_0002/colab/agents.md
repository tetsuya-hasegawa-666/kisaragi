# agents.md

## colab の役割

- この directory は `prj-kisaragi_0002` の `Colab` 実行用 script、runbook、notebook の正本を置く。

## 運用規則

- `Colab` に貼り付ける `runbook`、upload する notebook、補助 script はこの directory に集約する。
- `modeling/evidence/` は legacy evidence の保持先としてのみ扱い、新しい `Colab` script や notebook は保存しない。
- `Colab` 実行で生じる生成物、download 物、raw artifact はここに置かず、Drive 正本または evidence / testlog 側の規則へ従う。
