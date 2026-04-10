# 次回引き継ぎメモ

## 目的

- 今回の session 以後に引き継ぐ時、`prj-kisaragi_0002` の次の主作業だけを短く共有できるようにする。
- `MRL-1` から `MRL-9` は `p-done` とし、次段の `MRL-2S`、`MRL-10`、後続 `MRL-**` へ迷わず移るための補助メモとする。

## 次回の基準文書

- 恒久 truth は [project-truth.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\project-truth.md)
- plan / current / gate は [hi-ai-unified-blueprint.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\hi-ai-unified-blueprint.md)
- record-native `Colab` 正本は [da3_ngl_increpose_RB.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab\da3_ngl_increpose_RB.md)
- record-native `Colab` の実行 notebook は [da3_ngl_increpose_RB.ipynb](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab\da3_ngl_increpose_RB.ipynb)
- `correcting` の local product script / source inventory は [correcting_script_source_inventory.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\correcting\correcting_script_source_inventory.md)
- `modeling` の canonical pair source inventory は [da3_ngl_increpose_source_inventory.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab\da3_ngl_increpose_source_inventory.md)
- `MRL-10` は同 runbook の `.md/.ipynb` pair の `MRL-10 record-native DA3 route` section を使う
- `MRL-10` の script 編集時の参照契約は [hi-ai-unified-blueprint.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\hi-ai-unified-blueprint.md) の `Increpose Path Handoff Matrix` を正とし、再検査は [da3_increpose_path_contract_probe.py](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--testcode\prj-kisaragi_0002\da3_increpose_path_contract_probe.py) と関連 unittest を使う
- notebook cell、error、admin 実行結果の往復 log は [sharedlogs_da3-colab.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\sharedlogs_da3-colab.md)
- admin UX 手順は [admin-mrl-test-method.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\admin-mrl-test-method.md)
- admin evidence は [admin-mrl-test-evidence.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\admin-mrl-test-evidence.md)

## 引き継ぎ時点の確定事項

- `Colab` modeling canonical route は、sequence-anchor first / `1 frame = 1 record` / `DA3NESTED-GIANT-LARGE-1.1` の official API 基準へ切り替えた。
- 成立済みなのは `single-frame bootstrap` であり、これは最終目標ではなく `modeling 本機能` への通過点である。
- `MRL-1` と `MRL-2` は `correcting` phase の `p-done` であり、実 session 記録、`data-check`、calibration、`Google Drive` 転送、handoff bundle まで閉じている。
- `MRL-3` から `MRL-6` は `modeling` phase の `p-done` であり、bootstrap / install、bundle 読込、single-frame `3DGS` smoke、evidence bundle 取得まで閉じている。
- `MRL-7` は `multi-frame` densify と gaussian short optimization まで `p-done` である。
- `MRL-8` は `p-done` であり、`DA3 Colab` runbook 本体の前段で Drive 上の任意 session zip / session folder を script だけで選び、selected input を bootstrap 本体と `MRL-7` one-block の両方へ渡せる状態を閉じた。
- 現在の main target は `MRL-2S` と `MRL-10` であり、`correcting` の `10min` 実収録安定化と、`frame_record.jsonl + images` を正にした record-native `Colab` route を canonical 化し、`90度右回転` upright image 契約、legacy intrinsics 補正、`orientation_summary.json`、sequence anchor、adjacent continuity precheck、pre-merge gate を main runbook の `.md/.ipynb` pair に固定することである。camera pose / trajectory の事前推定も `DA3NESTED-GIANT-LARGE-1.1` の official API / CLI 基準へ統一する。
- `2026-04-11` 時点では `da3_ngl_increpose_RB` の path / reference 再検査を実施し、`HAUB` handoff matrix、contract probe、source test は clean である。directory handoff は `batch_work_dir = chunk_runs/<batch_name>/`、`chunk_out_dir = chunk_runs/<batch_name>/<chunk_name>/` を基準とし、legacy manifest が chunk path や `chunk_0005_*` suffix dir を持っていても reader が吸収する。以後は script / notebook source 編集後に同じ検査を必ず回す。
- `2026-04-11` からは merge / graph の final access contract を `probe_root/final_outputs/#10-1/`、`probe_root/final_outputs/#11-1/` の stage root へ寄せる。各 stage root は `re_access/` と `persist_only/` に分かれ、`persist_only/` が canonical file 実体、`re_access/` が handoff manifest / resume pointer である。
- script inventory は `correcting` 用と `modeling` 用を分離し、`correcting` 側は現状をありのまま記録する。`HAUB` は統合入口、product 側 inventory は詳細参照面とする。
- `MRL-**` は細かく固定せず大まかな順番だけを置き、実測で見えた課題の大小に応じて `MRL` / `mRL` を切り直す。
- ただし後続 `MRL` でも UX 到達品質は元の目標に沿わせる。特に modeling では、利用者が主空間の見え方、主カメラ経路、処理状態、次 action を迷わず把握できる方向を維持する。
- 後続 `MRL-**` で最低限残る項目は、`multi-route` 比較、`selected_route.json` 固定、request 起点 UX、`job_status.json` と waiting ring、download URL を含む result 返却、`SpacePackage` / `TrajectoryPackage` / `ReviewArtifact` handoff、reviewing viewer 実装、`gs_ply` を使う top camera renderer である。

## 到達済み

- [da3_ngl_increpose_RB.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab\da3_ngl_increpose_RB.md) は `sliding_window_incremental_seeded` を採用した canonical pair であり、chunk overlap を前 chunk の採択 pose で seed しながら進める。
- `Google Drive` shortcut 配下の zip から `session_root` を正規化できる。
- `Depth-Anything-3` repo clone、必要 dependency install、`depth_anything_3.api` import が通る。
- `T4` 上で `DA3NESTED-GIANT-LARGE-1.1` の `1 frame` 推論が通り、`summary.json`、`depth_preview.png`、`depth_raw.npy` を保存できる。
- `conf`、`intrinsics`、`extrinsics` が `None` でも bootstrap pass として扱う。
- `correcting` 実 data を使い、world back-projection、point export、`gsplat` rasterization、`gs_model` / `space_quality` / `SpacePackage` smoke artifact 生成、local download evidence 化まで通過した。
- この結果は `MRL-3` から `MRL-6` の `p-done` 根拠として正本へ反映済みである。

## 次回の主残件

- `MRL-9` は `p-done` であり、`infer_gs=True` route で `gs_ply/0000.ply`、`gs_video/0000_extend.mp4`、`scene.glb`、`exports/npz/results.npz` を保存でき、external viewer で開けるところまで確認済みである。
- 次の main target は `MRL-10` であり、`frame_record.jsonl + images` を正にした input 正規化、QC、sequence anchor、adjacent continuity check、official API による batch/chunk 実行、pre-merge gate、final merge を main runbook の `.md/.ipynb` pair へ固定することである。camera pose / trajectory も `DA3NESTED-GIANT-LARGE-1.1` だけで推定する。
- `sampling` / `intrinsics` / `projection` の route 比較、`benchmark_summary.json`、`selected_route.json` の本機能 close は `MRL-**` 側の後続課題として未達。
- request 元画面から `Google Drive` input directory / result directory を指定する UX は未実装。
- remote 実行中の `waiting ring`、現在 stage、更新時刻表示は未実装。
- `modeling/job_status.json` の厳密 schema と更新 timing は未固定。
- remote 完了後の `download URL` 返却導線は未実装。
- reviewing viewer で主空間、主カメラ経路、人物経路、same-time highlight、`attention point` を同じ review 文脈で扱う最終 UX は未実装。

## 次回の最初の 5 手

1. [sharedlogs_da3-colab.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\sharedlogs_da3-colab.md) の最下部を読んで、最新の `# codex v**` と `# admin` を確認する。
2. [hi-ai-unified-blueprint.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\hi-ai-unified-blueprint.md) で `MRL-2S` と後続 `MRL-**` の current_state を確認する。
3. record-native route を blank runtime から進める時は [da3_ngl_increpose_RB.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\colab\da3_ngl_increpose_RB.md) の `#1` から `#6` までを順に実行し、mount、config、input 選択、tree 作成、install、helper を固める。
4. `MRL-10` を進める時は同 runbook の `#7` と `#8` を順に実行し、full anchor、anchor QC、record manifest、chunk plan、precheck、`sliding_window_incremental_seeded` の chunk 実行が通ることを先に確認する。
5. giant production candidate は同 runbook の `#9`、`#10`、`#11` を順に実行し、overlap matching、global graph gate、final merge / review を進める。merge 証跡は `incremental_seed_trace_arc.csv`、`prepose_chunk_graph_solution_arc.csv`、`chunk_global_transforms_arc.csv`、`merge_summary.json`、`chunk_transform_quality_arc.csv` として残る。
6. `#10-1` と `#11-1` の directory で迷ったら、まず `final_outputs/#10-1/re_access/graph_contract_manifest.json` と `final_outputs/#11-1/re_access/stage_access_index.json` を見る。file 実体探索を先に始めず、manifest が指す canonical path を採用する。
7. script / notebook source を触る時は、最後に `python -m unittest C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--testcode\prj-kisaragi_0002\test_da3_increpose_path_contract_probe.py C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--testcode\prj-kisaragi_0002\test_da3_increpose_sources.py` を回し、`HAUB` handoff matrix と pair の参照整合を再確認する。

## 引き継ぎ上の重要判断

- shared log は main collaborative log だが、truth / plan / evidence の代替ではない。
- shared log で決まった持続事項は、同じ task 内で必ず正本へ反映する。
- shared log は header 以外を通常編集せず、下へ追記する。
- `# codex` 追記には `v**` を必ず付ける。
- `Colab` のような揮発 runtime では、trial の回避策を shared log に積むだけで終わらせず、真に必要だった最短 bootstrap を product 正本へ昇格する。

## 引き継ぎ時の禁止事項

- `MRL-1` から `MRL-6` の `p-done` を `reviewing` 完成や `system統合` 完成と誤認しない。
- shared log だけを見て gate 判定を動かさない。
- `COLMAP 4.0 + nerfstudio splatfacto` の旧 notebook を truth として再採用しない。
- shared log の途中へ要約や code を差し込まない。


