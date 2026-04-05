# agents.md

## colab の役割

- この directory は `prj-kisaragi_0002` の `Colab` 実行用 script、runbook、notebook の正本を置く。

## 運用規則

- `Colab` に貼り付ける `runbook`、upload する notebook、補助 script はこの directory に集約する。
- `runbook` は `.md` と `.ipynb` の pair を必須とし、`.md` を正本、`.ipynb` を同内容の実行 notebook として同じ task で同期する。
- `modeling/evidence/` は legacy evidence の保持先としてのみ扱い、新しい `Colab` script や notebook は保存しない。
- `Colab` 実行で生じる生成物、download 物、raw artifact はここに置かず、Drive 正本または evidence / testlog 側の規則へ従う。
- `modeling` の Drive 正本 top directory 名は modeling session 名そのものを使い、`trajectreview-modeling-session-YYYYMMDD_<slug>` 形式へそろえる。
- `probe_root` の自動生成や既存 `probe_root` 参照もこの命名を正とし、旧 suffix 付き命名を新規採用しない。
- `modeling` の main 処理完了条件は Drive 正本側の保存完了とし、local zip 作成や browser download は別段の任意 block へ分離する。
