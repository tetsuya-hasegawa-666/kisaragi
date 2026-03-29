# 次回引き継ぎメモ

## 目的

- 今回の session 以後に引き継ぐ時、`prj-kisaragi_0002` の次の主作業だけを短く共有できるようにする。
- `MRL-12` は `p-done` とし、次段の `MRL-13` へ迷わず移るための補助メモとする。

## 次回の基準文書

- 恒久 truth は [project-truth.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\project-truth.md)
- plan / current / gate は [ux-b2t-hypo.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\ux-b2t-hypo.md)
- `DA3 Colab bootstrap` の product 正本は [da3_colab_clean_bootstrap_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_clean_bootstrap_runbook.md)
- notebook cell、error、admin 実行結果の往復 log は [sharedlogs_da3-colab.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\sharedlogs_da3-colab.md)
- admin UX 手順は [admin-mrl-test-method.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\admin-mrl-test-method.md)
- admin evidence は [admin-mrl-test-evidence.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\admin-mrl-test-evidence.md)

## 引き継ぎ時点の確定事項

- `DA3Metric-Large` の `Colab` bootstrap は、`2026-03-29` に `T4` 上で `Step 1` から `Step 4` まで end-to-end 通過した。
- 成立済みなのは `single-frame bootstrap` であり、これは最終目標ではなく `modeling 本機能` への通過点である。
- `MRL-12` は、`correcting` 実 data から `3DGS` 系主空間モデル候補を smoke 生成し、admin が notebook / local download で生成物を取得できることを根拠に `p-done` とした。
- 現在の main target は `MRL-13` であり、`10s` 前後の整った実動画を使った `multi-frame` densify で、利用者が主空間の見え方と主カメラ経路を粗く把握できる再現モデルを admin がまず `PLY` viewer で確認する水準へ進めることである。
- `MRL-14` 以降は細かく固定せず `MRL-**` として大まかな順番だけを置き、実測で見えた課題の大小に応じて `MRL` / `mRL` を切り直す。
- ただし後続 `MRL` でも UX 到達品質は元の目標に沿わせる。特に modeling では、利用者が主空間の見え方、主カメラ経路、処理状態、次 action を迷わず把握できる方向を維持する。
- 後続 `MRL-**` で最低限残る項目は、`multi-route` 比較、`selected_route.json` 固定、request 起点 UX、`job_status.json` と waiting ring、download URL を含む result 返却、`SpacePackage` / `TrajectoryPackage` / `ReviewArtifact` handoff、reviewing viewer 実装である。

## 到達済み

- [da3_colab_clean_bootstrap_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_clean_bootstrap_runbook.md) は `Adopted Bootstrap v1` を持つ。
- `Google Drive` shortcut 配下の zip から `session_root` を正規化できる。
- `Depth-Anything-3` repo clone、必要 dependency install、`depth_anything_3.api` import が通る。
- `T4` 上で `DA3METRIC-LARGE` の `1 frame` 推論が通り、`summary.json`、`depth_preview.png`、`depth_raw.npy` を保存できる。
- `conf`、`intrinsics`、`extrinsics` が `None` でも bootstrap pass として扱う。
- `correcting` 実 data を使い、world back-projection、point export、`gsplat` rasterization、`gs_model` / `space_quality` / `SpacePackage` smoke artifact 生成、local download evidence 化まで通過した。
- この結果は `MRL-12` / `mRL-12.1` から `mRL-12.3` の `p-done` 根拠として正本へ反映済みである。

## 次回の主残件

- `10s` 前後の整った実動画から `multi-frame` で point cloud を densify し、`PLY` viewer でぼんやり見える再現モデルを確認する route は未着手。
- `sampling` / `intrinsics` / `projection` の route 比較、`benchmark_summary.json`、`selected_route.json` の本機能 close は `MRL-**` 側の後続課題として未達。
- request 元画面から `Google Drive` input directory / result directory を指定する UX は未実装。
- remote 実行中の `waiting ring`、現在 stage、更新時刻表示は未実装。
- `modeling/job_status.json` の厳密 schema と更新 timing は未固定。
- remote 完了後の `download URL` 返却導線は未実装。
- reviewing viewer で主空間、主カメラ経路、人物経路、same-time highlight、`attention point` を同じ review 文脈で扱う最終 UX は未実装。

## 次回の最初の 5 手

1. [sharedlogs_da3-colab.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\sharedlogs_da3-colab.md) の最下部を読んで、最新の `# codex v**` と `# admin` を確認する。
2. [ux-b2t-hypo.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\ux-b2t-hypo.md) の `MRL-13` を確認し、次段の target を `10s` 前後の整った実動画による `multi-frame` densify に合わせる。
3. `Colab` 側で `single-frame` の次として、複数 frame を sampling して world point cloud を統合し、`PLY` でぼんやり見える再現モデルを出す最小 route を設計する。
4. `MRL-13` で本当に必要になった追加確認だけを `mRL-13.**` として切り出し、後続の route 比較や UX 統合は `MRL-**` 側へ送る。
5. その後に `modeling/job_status.json` の schema、stage 名、waiting ring 更新条件、download URL 返却条件と、request 元の `input directory`、`result directory`、`route id` を束ねた request 生成 UX を設計する。

## 引き継ぎ上の重要判断

- shared log は main collaborative log だが、truth / plan / evidence の代替ではない。
- shared log で決まった持続事項は、同じ task 内で必ず正本へ反映する。
- shared log は header 以外を通常編集せず、下へ追記する。
- `# codex` 追記には `v**` を必ず付ける。
- `Colab` のような揮発 runtime では、trial の回避策を shared log に積むだけで終わらせず、真に必要だった最短 bootstrap を product 正本へ昇格する。

## 引き継ぎ時の禁止事項

- `MRL-12 p-done` を `modeling 完成` や `3DGS` 高品質 viewer 完成と誤認しない。
- shared log だけを見て gate 判定を動かさない。
- `COLMAP 4.0 + nerfstudio splatfacto` の旧 notebook を truth として再採用しない。
- shared log の途中へ要約や code を差し込まない。
