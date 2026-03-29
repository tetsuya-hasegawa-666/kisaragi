# 次回引き継ぎメモ

## 目的

- 今回の session 以後に引き継ぐ時、`prj-kisaragi_0002` の次の主作業だけを短く共有できるようにする。
- `DA3Metric-Large` の `Colab` bootstrap 成立を最終目標と誤認せず、`MRL-12` 以降の system 構築と UX 実装へ引き継ぐ。

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
- 現在の main target は、`MRL-12` の system 構築として `metric depth + world projection + 3DGS 系主空間モデル生成` を具体化し、`gs_model` を含む `SpacePackage` 実生成を成立させることである。
- `request 起点 UX`、`job_status`、`waiting ring`、`download URL` は、その後段で `MRL-11` から `MRL-13` を閉じるために実装する。

## 到達済み

- [da3_colab_clean_bootstrap_runbook.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--products\prj-kisaragi_0002\modeling\da3_colab_clean_bootstrap_runbook.md) は `Adopted Bootstrap v1` を持つ。
- `Google Drive` shortcut 配下の zip から `session_root` を正規化できる。
- `Depth-Anything-3` repo clone、必要 dependency install、`depth_anything_3.api` import が通る。
- `T4` 上で `DA3METRIC-LARGE` の `1 frame` 推論が通り、`summary.json`、`depth_preview.png`、`depth_raw.npy` を保存できる。
- `conf`、`intrinsics`、`extrinsics` が `None` でも bootstrap pass として扱う。
- ここまでで確認できたのは depth 推論 bootstrap までであり、`gs_model` を含む `SpacePackage` 実生成は未達である。
- この結果は `INITRL-1` / `mINITRL-1.2`、`MRL-11` / `mRL-11.1`、`MRL-12` / `mRL-12.2` の candidate evidence に反映済みである。

## 次回の主残件

- `MRL-12` の本来到達物である `gs_model` を含む `SpacePackage` 実生成 route は未実装。
- `depth_estimation_report.json`、`space_quality.json`、`gs_model`、`SpacePackage` を同じ route で揃える最小 system route が未定義である。
- request 元画面から `Google Drive` input directory / result directory を指定する UX は未実装。
- remote 実行中の `waiting ring`、現在 stage、更新時刻表示は未実装。
- `modeling/job_status.json` の厳密 schema と更新 timing は未固定。
- remote 完了後の `download URL` 返却導線は未実装。
- `single-frame` を超える複数 frame 実行、sampling / intrinsics route 比較、`benchmark_summary.json`、`selected_route.json` の本機能 close は未達。

## 次回の最初の 5 手

1. [sharedlogs_da3-colab.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\sharedlogs_da3-colab.md) の最下部を読んで、最新の `# codex v**` と `# admin` を確認する。
2. [ux-b2t-hypo.md](C:\Users\tetsuya\kisaragi\kisaragi-db\--devs\--tgpce-map\prj-kisaragi_0002\ux-b2t-hypo.md) の `MRL-11`、`MRL-12`、`MRL-13` を確認し、次段の target を `bootstrap` 単体ではなく `MRL-12 の system 構築` に合わせる。
3. `MRL-12` の生成物として `depth_estimation_report.json`、`space_quality.json`、`gs_model`、`SpacePackage` を明確化し、最小実行 route を設計する。
4. `Colab` 側では `single-frame` の次として、`multi-frame` 実行、world projection、`3DGS` 系主空間モデル生成、result zip / URL 返却の最小 route を設計する。
5. その後に `modeling/job_status.json` の schema、stage 名、waiting ring 更新条件、download URL 返却条件と、request 元の `input directory`、`result directory`、`route id` を束ねた request 生成 UX を設計する。

## 引き継ぎ上の重要判断

- shared log は main collaborative log だが、truth / plan / evidence の代替ではない。
- shared log で決まった持続事項は、同じ task 内で必ず正本へ反映する。
- shared log は header 以外を通常編集せず、下へ追記する。
- `# codex` 追記には `v**` を必ず付ける。
- `Colab` のような揮発 runtime では、trial の回避策を shared log に積むだけで終わらせず、真に必要だった最短 bootstrap を product 正本へ昇格する。

## 引き継ぎ時の禁止事項

- `single-frame bootstrap pass` を `modeling 完成` や `3DGS` 生成確認完了と誤認しない。
- shared log だけを見て gate 判定を動かさない。
- `COLMAP 4.0 + nerfstudio splatfacto` の旧 notebook を truth として再採用しない。
- shared log の途中へ要約や code を差し込まない。
