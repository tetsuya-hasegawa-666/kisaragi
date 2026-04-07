# agents.md

## colab の役割

- この directory は `prj-kisaragi_0002` の `Colab` 実行用 script、runbook、notebook の正本を置く。

## 運用規則

- `Colab` に貼り付ける `runbook`、upload する notebook、補助 script はこの directory に集約する。
- `runbook` は `.md` と `.ipynb` の pair を必須とし、`.md` を正本、`.ipynb` を同内容の実行 notebook として同じ task で同期する。
- 現行 canonical pair は `da3_ngl_runbook.md` と `da3_ngl_runbook.ipynb` とする。
- `da3_ngl_runbook` の設計契約書は `da3_ngl_runbook_design_contract.md` とし、stage 責務、source-sync 対象、変更ゲートの正本とする。
- `da3_runbook_sources/` は canonical pair を局所 source から同期する authoring 面とし、`#5-1`、`#6-1`、`#12-2` のような再出現しやすい source はここから `sync_da3_runbook_sources.py` で pair へ反映する。
- canonical pair を直接編集した時は、同じ task で `da3_runbook_sources/` 側との整合も戻す。
- `modeling/evidence/` は legacy evidence の保持先としてのみ扱い、新しい `Colab` script や notebook は保存しない。
- `Colab` 実行で生じる生成物、download 物、raw artifact はここに置かず、Drive 正本または evidence / testlog 側の規則へ従う。
- `modeling` の Drive 正本 top directory 名は modeling session 名そのものを使い、`trajectreview-modeling-session-YYYYMMDD_<slug>` 形式へそろえる。
- `probe_root` の自動生成や既存 `probe_root` 参照もこの命名を正とし、旧 suffix 付き命名を新規採用しない。
- `modeling` の main 処理完了条件は Drive 正本側の保存完了とし、local zip 作成や browser download は別段の任意 block へ分離する。
