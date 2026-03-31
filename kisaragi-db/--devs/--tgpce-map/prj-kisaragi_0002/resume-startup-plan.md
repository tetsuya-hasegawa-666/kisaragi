# 次回引き継ぎメモ

## 目的

- 今回の session 以後に引き継ぐ時、`prj-kisaragi_0002` の次の主作業だけを短く共有できるようにする。
- `MRL-1` から `MRL-8` は `p-done` とし、次段の `MRL-2S` と後続 `MRL-**` へ迷わず移るための補助メモとする。

## 次回の基準文書

- 恒久 truth は [project-truth.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\project-truth.md)
- plan / current / gate は [ux-b2t-hypo.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\ux-b2t-hypo.md)
- `DA3 Colab bootstrap` の product 正本は [da3_colab_evid_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_evid_runbook.md)
- admin が Colab へ貼り付ける参照版は [da3_colab_ref_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_ref_runbook.md)
- notebook cell、error、admin 実行結果の往復 log は [sharedlogs_da3-colab.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\sharedlogs_da3-colab.md)
- admin UX 手順は [admin-mrl-test-method.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\admin-mrl-test-method.md)
- admin evidence は [admin-mrl-test-evidence.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\admin-mrl-test-evidence.md)

## 引き継ぎ時点の確定事項

- `DA3Metric-Large` の `Colab` bootstrap は、`2026-03-29` に `T4` 上で `Step 1` から `Step 4` まで end-to-end 通過した。
- 成立済みなのは `single-frame bootstrap` であり、これは最終目標ではなく `modeling 本機能` への通過点である。
- `MRL-1` と `MRL-2` は `correcting` phase の `p-done` であり、実 session 記録、`data-check`、calibration、`Google Drive` 転送、handoff bundle まで閉じている。
- `MRL-3` から `MRL-6` は `modeling` phase の `p-done` であり、bootstrap / install、bundle 読込、single-frame `3DGS` smoke、evidence bundle 取得まで閉じている。
- `MRL-7` は `multi-frame` densify と gaussian short optimization まで `p-done` である。
- `MRL-8` は `p-done` であり、`DA3 Colab` runbook 本体の前段で Drive 上の任意 session zip / session folder を script だけで選び、selected input を bootstrap 本体と `MRL-7` one-block の両方へ渡せる状態を閉じた。
- 現在の main target は `MRL-2S` と後続 `MRL-**` であり、`correcting` の `10min` 実収録安定化と、gaussian parameter の formalization / viewer 寄せを進めることである。
- `MRL-**` は細かく固定せず大まかな順番だけを置き、実測で見えた課題の大小に応じて `MRL` / `mRL` を切り直す。
- ただし後続 `MRL` でも UX 到達品質は元の目標に沿わせる。特に modeling では、利用者が主空間の見え方、主カメラ経路、処理状態、次 action を迷わず把握できる方向を維持する。
- 後続 `MRL-**` で最低限残る項目は、`multi-route` 比較、`selected_route.json` 固定、request 起点 UX、`job_status.json` と waiting ring、download URL を含む result 返却、`SpacePackage` / `TrajectoryPackage` / `ReviewArtifact` handoff、reviewing viewer 実装である。

## 到達済み

- [da3_colab_evid_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_evid_runbook.md) は `Adopted Bootstrap v1` を持つ。
- `Google Drive` shortcut 配下の zip から `session_root` を正規化できる。
- `Depth-Anything-3` repo clone、必要 dependency install、`depth_anything_3.api` import が通る。
- `T4` 上で `DA3METRIC-LARGE` の `1 frame` 推論が通り、`summary.json`、`depth_preview.png`、`depth_raw.npy` を保存できる。
- `conf`、`intrinsics`、`extrinsics` が `None` でも bootstrap pass として扱う。
- `correcting` 実 data を使い、world back-projection、point export、`gsplat` rasterization、`gs_model` / `space_quality` / `SpacePackage` smoke artifact 生成、local download evidence 化まで通過した。
- この結果は `MRL-3` から `MRL-6` の `p-done` 根拠として正本へ反映済みである。

## 次回の主残件

- runbook は Drive 上の特定 path を hardcode していたため、任意 input を script だけで差し替える前段 block が未完成である。
- `sampling` / `intrinsics` / `projection` の route 比較、`benchmark_summary.json`、`selected_route.json` の本機能 close は `MRL-**` 側の後続課題として未達。
- request 元画面から `Google Drive` input directory / result directory を指定する UX は未実装。
- remote 実行中の `waiting ring`、現在 stage、更新時刻表示は未実装。
- `modeling/job_status.json` の厳密 schema と更新 timing は未固定。
- remote 完了後の `download URL` 返却導線は未実装。
- reviewing viewer で主空間、主カメラ経路、人物経路、same-time highlight、`attention point` を同じ review 文脈で扱う最終 UX は未実装。

## 次回の最初の 5 手

1. [sharedlogs_da3-colab.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\sharedlogs_da3-colab.md) の最下部を読んで、最新の `# codex v**` と `# admin` を確認する。
2. [ux-b2t-hypo.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\ux-b2t-hypo.md) で `MRL-2S` と後続 `MRL-**` の current_state を確認する。
3. [da3_colab_evid_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_evid_runbook.md) の `準備確認 2` から `準備確認 4` を使えば、任意 selected input から blank runtime を再開できることを前提にする。
4. gaussian parameter の formalization、viewer で読む scene 形式、multi-view / 長時間 optimization のどこを次の visible target に置くかを決める。
5. 並行して `modeling/job_status.json` の schema、stage 名、waiting ring 更新条件、download URL 返却条件と、request 元の `input directory`、`result directory`、`route id` を束ねた request 生成 UX を設計する。

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
