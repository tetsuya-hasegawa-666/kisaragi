# agents.md

## colab の役割

- この directory は `prj-kisaragi_0002` の `Colab` 実行用 script、runbook、notebook の管理文書と根拠情報を置く。

## 運用規則

- `Colab` に貼り付ける `runbook`、upload する notebook、補助 script はこの directory に集約する。
- `runbook` は `.md` と `.ipynb` の pair を必須とし、`.md` を説明付き runbook、`.ipynb` を同内容の実行 notebook として同じ task で同期する。
- 現行 canonical pair は `da3_ngl_increpose_RB.md` と `da3_ngl_increpose_RB.ipynb` とする。
- `da3_ngl_prepose_RB.md` / `.ipynb` と `da3_ngl_optpose_RB.md` / `.ipynb` は legacy / 比較用 pair とし、canonical pair を置き換えずに並行保持してよい。
- `da3_ngl_increpose_RB` の設計契約書は `da3_ngl_runbook_design_contract.md` とし、stage 責務、source-sync 対象、変更ゲートを定義する管理文書とする。
- `da3_increpose_sources/` は canonical pair を局所 source から同期する authoring 面とし、cell ごとの code file、markdown file、manifest、source-sync script、inventory script を持つ。canonical pair を直接編集した時も、同じ task でこの directory へ戻して整合を回復する。
- `da3_runbook_sources/` と `da3_optpose_sources/` は prepose / optpose の比較系 authoring 面として残し、検証や退避のための pair を再生成できる状態を保つ。
- `da3_ngl_optpose_RB` の出力 tree は `immutable run / release 実体 + current/latest pointer + tree schema version` を基本とし、`10_validation/runs/<run_id>/` を canonical validation 実体、`20_delivery/*` を delivery 面とする。旧 path は notebook 互換のため compatibility alias を残してよいが、新規 code は canonical dir を優先する。
- `da3_ngl_increpose_RB` は `sliding_window_incremental_seeded` を canonical route とし、`#8-9` で前 chunk の adopted pose を次 chunk の context へ seed しながら漸次実行し、`#9-1` で overlap matching、`#10-1` で chunk-to-world graph / gate、`#11-1` で merge を行う。
- `modeling/evidence/` は legacy evidence の保持先としてのみ扱い、新しい `Colab` script や notebook は保存しない。
- `Colab` 実行で生じる生成物、download 物、raw artifact はここに置かず、Drive 保持先または evidence / testlog 側の規則へ従う。
- `modeling` の Drive 保持先 top directory 名は modeling session 名そのものを使い、`trajectreview-modeling-session-YYYYMMDD_<slug>` 形式へそろえる。
- `probe_root` の自動生成や既存 `probe_root` 参照もこの命名を正とし、旧 suffix 付き命名を新規採用しない。
- `modeling` の main 処理完了条件は Drive 保持先側の保存完了とし、local zip 作成や browser download は別段の任意 block へ分離する。
