# da3_ngl_prepose_RB design contract

この文書は `da3_ngl_prepose_RB.md` / `da3_ngl_prepose_RB.ipynb` を source 根拠情報から再構築する時の authoring 契約詳細とする。日常運用で最初に見る要約面は `HAUB` の modeling 用一覧表直後の契約表とし、本書はその補助詳細を担う。

## 目的

- `da3_runbook_sources/` を canonical source とし、notebook 上の code cell と markdown cell の両方を管理対象にする。
- 各 markdown cell は対応する `#No`、その直前の `#No`、その直後の `#No` を先頭に持ち、複数 pattern は `#9-1..#9-5` のような最短表現で示す。
- `#6 Shared Helpers` を camera trajectory / pose / intrinsics / anchor basis の唯一の共通契約面とし、`#7`、`#12`、`#13`、`#14` が同じ参照面で動くようにする。
- `#7matching-1` は `#7` の直後で 2 chunk overlap pose を同一座標系へ再現する事前 matching 面とし、chunk A/B の `pred_extrinsics.npy` と `chunk_input_frames.csv` から overlap 対応、relative transform、matching residual を固定 artifact として残す。
- `#13` と `#14` は merge route を 1 本固定で閉じず、baseline route と `DA3 NGL predicted trajectory experimental route` の 2 本を比較できる authoring 契約で保つ。baseline は fallback / judge、`DA3` は merge 主座標候補として扱う。
- `#13-1` は route compare の結果を `prepose_chunk_graph_solution_arc.csv`、`prepose_chunk_graph_edges_arc.csv`、`prepose_chunk_graph_summary.json` として固定し、`#14-1` はその graph artifact を優先消費する。graph artifact には `graph_parent_chunk_name`、`relative_scale`、`relative_translation_norm`、`relative_rotation_deg` を含める。
- `#7matching-1` は matching 結果を `overlap_pair_metrics_arc.csv`、`trajectory_points_arc.csv`、`transform_b_to_a.npy`、`trajectory_match.png`、`matching_summary.json` として `persist_root/01_anchor/07matching/` に固定する。summary には `relative_scale`、`relative_translation_norm`、`relative_rotation_deg`、pre/post residual を含める。
- `HAUB` の script 一覧表は `correcting` 用と `modeling` 用を分離し、`modeling` 側は cell ごとの役割だけでなく、主要 data 名、reference directories、主要 output / handoff を含む 1 表で管理する。`correcting` 側は別の local product inventory を参照し、両表の思想をそろえて参照面の取り違えを防ぐ。

## source 根拠情報

| item | path | role |
| --- | --- | --- |
| code manifest | `da3_runbook_sources/cell_manifest.json` | code cell token と source file の対応 |
| markdown manifest | `da3_runbook_sources/markdown_manifest.json` | markdown cell の順序、対応 token、前後参照 |
| code source | `da3_runbook_sources/cells/*.py` | 各 code cell の根拠情報 |
| markdown source | `da3_runbook_sources/markdown/*.md` | 各 markdown cell の根拠情報 |
| sync utility | `da3_runbook_sources/sync_da3_runbook_sources.py` | source 根拠情報から pair を再構築する |
| inventory utility | `da3_runbook_sources/build_inventory.py` | code / markdown inventory を生成する |
| HAUB integrated tables | `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/hi-ai-unified-blueprint.md` | `correcting` 用 / `modeling` 用の統合入口を管理する |
| correcting inventory | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/correcting_script_source_inventory.md` | local product script / source の現状をありのまま追う |

## markdown cell rule

- markdown source file は先頭 3 行を必須とする。
- 1 行目は `#No: ...`
- 2 行目は `前: ...`
- 3 行目は `次: ...`
- 複数連番は `#4-1..#4-2` のように最短表現で書く。
- markdown 本文は、その直後の code cell 群の実働内容と出力契約に合わせる。

## 再構築 rule

- `sync_da3_runbook_sources.py` は markdown cell と code cell を source 根拠情報から順に組み立て、`.md` と `.ipynb` を同時更新する。
- notebook companion を直接編集した時は、その内容を `da3_runbook_sources/` 側へ戻すか、再度 source 根拠情報に寄せて同期し直す。
- inventory 更新時は `build_inventory.py` を再実行し、`da3_ngl_runbook_source_inventory.md` を同じ task で更新する。
- `#7matching-1` は `#13-1` と独立に実行できる診断面とし、input path が未指定または chunk artifact が未生成の時は `status: skipped` と `reason: matching_inputs_missing` を返して top-to-bottom 実行を壊さない。
- `#13-1` は pre-merge judge 面とし、最低でも `route_label`、`fallback_used`、`center_rmse`、`rotation_dir_residual`、`owner_record keep` に関わる judge 指標を baseline / experimental の両 route で比較できるように保つ。比較結果は `premerge_route_compare_arc.csv` と `premerge_route_compare_summary.json` に残す。
- `#13-1` はさらに `chunk_to_world` の事前整合 graph artifact を出し、`chunk_name`、`graph_parent_chunk_name`、`route_label`、`fallback_used`、`t00..t33`、overlap / non-overlap residual 指標、`relative_scale`、`relative_translation_norm`、`relative_rotation_deg` を残す。
- `#14-1` は merge engine 面とし、route 切替を config か route label で明示し、`prepose_chunk_graph_solution_arc.csv` を優先読み込みして `chunk_global_transforms_arc.csv`、`chunk_transform_quality_arc.csv`、`merge_route_compare_arc.csv`、`merge_summary.json` の各出力に route 判定と fallback の有無、chunk 間 relative transform を残すようにする。
- `HAUB` の `modeling` 用一覧表を更新する時は、少なくとも `role`、`key data names`、`reference directories`、`main outputs / handoff` の 4 列を維持し、runbook の参照面変更を同じ task で反映する。
- `correcting` 側で local product script / source を更新した時も、同じ 4 列を `correcting_script_source_inventory.md` と `HAUB` の correct 用一覧表へ同時反映する。
- 各 row では、どの reference directory を見ているかを曖昧名ではなく `persist_root/01_anchor`、`pipeline_root/manifests` のような具体 path で書く。
