# ux_b2t-hypo.md

## 文書の役割

この文書は `prj-kisaragi_0002` プロジェクトの goal、plan、current、evidenceを、1 つに統合した正本とする。

## current_state

### 役割

- `project-truth`とgoalからBDDにより実現に必要なUXを分解抽出しマイルストーンを置き、末端周辺をTDDでテスト計画してBDDマイルストーンをさらに小分解した計画と、そのテスト結果および現在の状態（project 固有 decision 要約）を統合的に記載する
- 基本的な考え方は上記だが、規模や内容によって柔軟に対応可能だが、要素の抜け漏れや忘れが起こらないように対応する
- `prj-kisaragi_0002` は、主空間再構成と経路レビューを 4 段階一括処理で扱う project とする
- 中核 UX は、`SessionPackage`、`SpacePackage`、`TrajectoryPackage`、`ReviewArtifact` が、屋外作業者や作業機の作業結果をレビューが平易な操作で臨場感あるレビュー体験とする
- 恒久仕様、入口方針、app 責務、artifact 契約は `project-truth.md` を正本とし、この章では現在状態、未完 gate、優先順位、未解決論点だけを扱う
- project 固有の current と decision はこの章へ集約し、shared governance 文書や他 category へ重複配置しない

### 疑問点不整合一覧

| id | 論点 | 影響 | 現在の扱い | admin 状態 | 関連文書 |
| --- | --- | --- | --- | --- | --- |
| `ISS-001` | `InputPackaging` の入口を `correcting` 中心へ寄せた後、統合 app / legacy intake をどこまで同格に扱うか | `InputPackaging` の UX、truth、後段説明 | admin 判断により、開発中から実使用まで全入口を開けたまま併存させ、説明順だけを運用上の既定に留める | `close` | `project-truth.md`, `admin-mrl-test-method.md` |
| `ISS-002` | `Google Drive` 転送先の document grant を持続前提にするか | `MRL-2` の実運用可否 | admin 判断により grant 持続前提を捨て、`転送先を選択` を毎回必須にする | `close` | `project-truth.md`, `admin-mrl-test-evidence.md` |
| `ISS-003` | `Google Drive` 側は zip、端末側は `<session_id>/` であり、どの段階で unzip を正規化するか | handoff 運用、admin 手順、実装分担 | `modeling` の `Colab bootstrap package` が unzip と配置正規化を担う方針へ決定した | `close` | `project-truth.md`, `admin-mrl-test-method.md` |
| `ISS-005` | `Colab all-in modeling` package と `correcting` の PC install package の配布形式をどこまで共通化するか | install / bootstrap UX の粒度、導入 UX | 利用者主導 `MRL` 配下の準備 UX として扱い、package 構成は `0002` 内で設計を継続する | `small-open` | `project-truth.md`, `ux-b2t-hypo.md` |
| `ISS-004` | `疑問点不整合一覧` の粒度を `MRL` closeout と同じ粒度まで細かくするか | 文書運用コスト | 現在は admin 判断が要るものと Codex の小疑問だけを集約する | `no judge` | `AGENTS.md`, `ux-b2t-hypo.md` |
| `ISS-006` | Android 標準保存画面で `Google Drive` provider へ切り替える操作が初見利用者に分かりにくい | 多人数展開時の導入 UX | 現時点は手順明記のみ。利用者が増えたら help 導線を追加する | `small-open` | `admin-mrl-test-method.md`, `project-truth.md` |

### 現在の重点

- `tu1` から `tu16` と `td1` から `td8` は contract 実装、test、routing 実行で成立したが、admin `UX check` 未完のため対応 `MRL` / `mRL` は `p-done` または `i-pass` に上げず `active` として扱う
- 旧 `MRL-1` から `MRL-14` は phase と手段が混在していたため、現在は `correcting`、`modeling`、`reviewing`、`system統合` の UX phase を見出しにし、その中へ複数 `MRL` を並べる
- `correcting` は `MRL-1` と `MRL-2` で扱い、前者が現場記録 / `data-check` / calibration 診断、後者が `Google Drive` 転送 / handoff bundle を担当する
- `modeling` は `MRL-3` から `MRL-7` で扱い、`MRL-3` が bootstrap / install、`MRL-4` が bundle 読込 / request preflight / directory intake、`MRL-5` が single-frame `3DGS` smoke、`MRL-6` が evidence bundle 取得、`MRL-7` が `multi-frame` densify を担当する
- `reviewing` は後続 `MRL-**` で、実 `ReviewArtifact` 読込と viewer UX を扱う
- `system統合` も後続 `MRL-**` で、4 app の end-to-end 導線と統合 UI を扱う
- 4 app 骨格、role-specific UX、統合 app overview は独立 `MRL` ではなく、各 flow の補助要素または後続 `MRL-**` の統合 UX として扱う
- `trajectreview-correcting` の現在 focus は、収録停止後の待ち時間短縮と、`品質確認` / 一覧更新 / 転送 UX の安定化である
- `品質確認` は lightweight 判定を先に返し、`frame画像群` は転送要求時だけ生成する構成へ切り替えた
- 保存済み data 一覧の `▲` は lightweight `品質確認` 再実行で更新し、軽微な項目や `images/` 未生成だけでは付けない運用へ切り替えた
- `Google Drive` 転送は都度 `転送先を選択` 前提へ切り替え、転送 UX は成立したが、多人数向け help は未着手である
- `MRL-1` の範囲では、`trajectreview-correcting` 単体で source session を保存し、`sensor_quality.json`、`session_package.json`、`space_handoff_manifest.json` を生成し、修正指示と calibration 診断を返せる実装がある
- `MRL-1` の calibration export interface は、一時要件を吸収し、`arcore_pose.jsonl` nested schema、`camera_calibration_summary.json`、`frame_pose_index.csv`、`images/`、path pointer を含む handoff へ更新した
- `MRL-1` では `intrinsics` 不足が `実取得失敗`、`集計上の見え方`、`calibration export 実装前 data` のどれかを切り分ける診断と、shared camera route の intrinsics 実収集までを扱う
- `MRL-2` の範囲では、`trajectreview-correcting` 単体で `サンプリング条件設定 / スマホ内保存先選択 / 転送対象準備 -> 現場撮影データ保存 + data-check -> 品質確認済み data の複数選択 -> Google Drive 転送先選択 + 転送実行 -> handoff bundle` を閉じる
- `trajectreview-modeling` は `Colab all-in` を主 route とし、PC 側は source、config、auto-install package、証跡の正本を保持する
- `trajectreview-modeling` は preflight artifact として `experiment_manifest.json`、`da3_input_manifest.json`、`benchmark_summary.json`、`selected_route.json`、Colab notebook / import helper / bootstrap package を持つ
- Colab notebook の `CONFIG` は `session_root` と `result_root` を最小入力とし、残りの route 情報は session bundle 内の artifact から自動で補完する
- 既存の `COLMAP 4.0 + nerfstudio splatfacto` notebook は参考ひな形であり、`DA3Metric-Large` modeling の truth ではない
- `DA3Metric-Large` の `Colab` 実装は greenfield とし、`Codex` が script / notebook を作成し、admin が `Colab` 実行結果を shared worklog に貼り戻す往復で詰める
- `2026-03-29` 時点で、`trajectreview-correcting` で取得した session `session-20260328-103250.zip` を入力に、`DA3Metric-Large` single-frame depth、world back-projection、point export、`gsplat` rasterization、`gs_model` / `space_quality` / `SpacePackage` smoke artifact 生成まで通過した
- 上記により、`correcting` phase は `MRL-1` と `MRL-2` が `p-done` で成立済みと読む
- `modeling` phase では、bootstrap / install、実 bundle 読込、single-frame `3DGS` smoke、artifact 取得までを `MRL-3` から `MRL-6` の `p-done` として扱う
- 現在の主作業は `modeling` phase の `MRL-7` であり、`10s` 前後の整った実動画による `multi-frame` densify を first target に置く
- shared worklog は project に対する truth / plan / evidence の正本ではないが、共同作業の保持情報としては authoritative な log であり、正本反映の根拠として保持する
- shared worklog の置き場は `--tgpce-map/prj-kisaragi_0002/` 直下とし、file 名は `sharedlogs_<thema>.md` 形式に統一する
- 現在の `DA3Metric-Large` `Colab` thread の main worklog は `sharedlogs_da3-colab.md` である
- shared worklog は読みやすさのために定型 header を持ち、header より下は `# codex` または `# admin` 見出しで末尾追記のみとする
- 採用判断、gate 状態、contract 変更、manual 変更は必ず対応する正本文書へ別途反映する
- shared worklog は定期的に振り返り、有益部分を正本や evidence へ反映済みなら old 本文を削除または reset してよい
- `Colab` のように runtime が揮発する route では、partial recovery の積み上げではなく fresh runtime からの最短 clean bootstrap を canonical route とする
- 上記 route では、trial 往復の shared worklog と別に、`--products/prj-kisaragi_0002/modeling/` 配下へ `最小 clean bootstrap runbook` を保持し、admin が次回は先頭から再実行できる形に収束させる
- `最小 clean bootstrap runbook` は `candidate` と `adopted` を分け、admin 実測で end-to-end が通った手順のみを `truly pass` 扱いにする
- 現在の `DA3Metric-Large` `Colab bootstrap` の正本は `--products/prj-kisaragi_0002/modeling/da3_colab_clean_bootstrap_runbook.md` とする
- 現在の `DA3Metric-Large` `Colab bootstrap` 実行は、`MRL-3` の bootstrap / install、`MRL-4` の directory intake、`MRL-5` の single-frame `3DGS` smoke の candidate evidence 収集を兼ねる
- `ISS-003` の unzip / 配置正規化責務は `modeling` の `Colab bootstrap package` が担う
- `trajectreview-modeling` の本機能 gate は、単一 route の一括 close ではなく、`比較基盤`、`比較実験`、`採用 route の運用化` の 3 段で閉じる
- `trajectreview-reviewing` は summary と stub 読込までは持つが、実 `ReviewArtifact` viewer と同時刻ハイライト操作は未実装である

### 決定済み運用

- `InputPackaging` の入口は `correcting`、統合 app、legacy intake を閉じずに併存させる
- `Google Drive` 転送先 file の document grant は保持前提にせず、毎回 `転送先を選択` で指定する
- `Google Drive` 転送 zip の既定名は `trajectreview-correcting-session-YYYYMMDD-HHMMSS.zip` とし、custom 名でも `-session-YYYYMMDD-HHMMSS` suffix を必須にする
- `reference_isensorium_verified_20260325` 配下の recording 実装は吸収済みとし、現行正規は `correcting`、`python`、`correcting/scripts`、`correcting-test` とする
- `prj-kisaragi_0002` の正本文書は `--tgpce-map/prj-kisaragi_0002/` に集約する

### 阻害要因の境界

- `DA3Metric-Large` を first target とする depth 基盤は定まったが、最終採用する sampling / intrinsics route は未決定である
- `DA3Metric-Large` の初回 `Colab` probe は一時確認であり、最終採用 route や truth を意味しない
- `DA3Metric-Large` の初回 `Colab` probe` は `numpy` ABI 不整合を越えたが、次段では probe cell 側の不要な `pkg_resources` import と runtime package 解決の不整合で `Cell C` import check が失敗している
- 次段の `Colab` probe は official repo clone、`numpy<2` 固定、runtime restart を維持しつつ、`pkg_resources` を明示 import しない最小 import check と runtime site-packages の実測確認へ切り替える
- runtime 実測により `Python 3.12` と `/usr/local/lib/python3.12/dist-packages` は整合していることが分かった。現在の blocker は `DepthAnything3` import 時に `export.gs -> moviepy -> pygame` を eager import して落ちる点である
- 次段の `Colab` probe は、推論に不要な `gs` export import を lazy 化するため、`depth_anything_3/utils/export/__init__.py` を部分置換ではなく file 上書き patch で差し替え、import / 1 frame 推論を再確認する
- `gs` eager import は外せたが、次段では `export.colmap -> pycolmap` の eager import が blocker になっている
- 次段の `Colab` probe は export module 全体を lazy import 化し、推論確認時に `pycolmap`、`moviepy`、`pygame` などの export 依存を読まない形へ切り替える
- export module 全体の lazy import 化は成立した。現在の blocker は `depth_anything_3.utils.io.output_processor` が要求する `addict` の未install である
- 次段の `Colab` probe は install をやり直さず、`addict` を追加 install して import / 1 frame 推論確認を続行する
- `addict` は install 済みとなり、現在の blocker は `depth_anything_3.utils.pose_align` が要求する `evo` の未install である
- 次段の `Colab` probe は install をやり直さず、`evo` を追加 install して import / 1 frame 推論確認を続行する
- `evo` は install 済みとなり、`Cell C` の import check は通過した。現在の blocker は `Cell D` の `SESSION_ROOT` が placeholder のままで、`images/` 実 path を指していない点である
- `Inspect Cell` 実行により `/content/drive/MyDrive/trajectreview/input` は存在しないことが分かった。現在の blocker は `Google Drive` 上の input root path 仮定が外れている点である
- 次段の `Colab` probe は code 修正ではなく、`Drive mount` 状態、使用 account、`MyDrive` / shared drive 上の実保存先を切り分け、`session_package.json` 所在確認により実 `session_root` を特定したうえで 1 frame 推論へ進む
- `/content/drive/MyDrive` 自体が `False` と判明したため、現在の最優先 blocker は `Drive mount` 未成立または auth 不整合である
- 次段の `Colab` probe は `force_remount` の再実行と mount 後 path 再確認を先に行い、その後に実 `session_root` 特定へ戻る
- `force_remount` 後に `/content/drive/MyDrive` は可視化されたため、`Drive mount` blocker は解消した
- 現在の blocker は、`MyDrive` 上のどこに実 session data があるか未特定な点であり、`Data_Correcting_System.zip` と `Colab Notebooks` を含む実 path 探索へ移っている
- `MyDrive` 直下探索では `session_package.json` などは 0 件で、`Data_Correcting_System.zip` は見つかったが無関係 file と判明した
- 次段の `Colab` probe は、`Colab Notebooks` 配下と `MyDrive` 全体から `trajectreview`、`session`、`camera_calibration_summary.json`、`frame_pose_index.csv`、`session_package.json` を手掛かりに実 data path を再探索する
- admin 提示の Google Drive folder URL があり、その folder が `共有アイテム` 側または shortcut 側にだけ存在して `MyDrive` 直下へ見えていない可能性がある
- 次段の `Colab` probe は `.shortcut-targets-by-id` と account / shortcut 状態を確認し、mount account と実 folder 可視性を切り分ける
- admin から `ショートカット追加済み`、`account 正しい` が確認されたため、次段は `.shortcut-targets-by-id/<folder-id>/` の直接確認で実 path を特定する
- `.shortcut-targets-by-id/<folder-id>/trajectreview/correcting/session-20260328-103250.zip` が実入力候補として見えたため、次段は Colab 作業用 directory への unzip / `session_root` 正規化へ進む
- zip 展開と `session_package.json` 探索により、実 `session_root` は `/content/trajectreview_input/session-20260328-103250/trajectreview` と確定した
- `images/` existence check は通過し、`image_count 182`、`first_image frame_000009.jpg` まで確認できた
- 現在の blocker は data path ではなく、`Cell D` 実行時の kernel 側で `depth_anything_3` module 解決が外れている点である
- `/content/Depth-Anything-3` の repo path 自体が消えていたため、原因は import 文脈だけでなく `Colab` 揮発 runtime による repo / custom install の消失と判断する
- 次段の `Colab` probe は、repo clone と custom dependency 再投入をまとめて再bootstrap し、その後に import check と 1 frame 推論を再実行する
- `Colab` 側の partial recovery を延々と積むより、ここまでで真に必要だった command を再合成した `最小 clean bootstrap runbook` を product 文書として維持する方針へ切り替える
- admin は `GPU` を選べるが、現段階は `CPU` 前提で bootstrap / import / `1 frame` 推論確認を進める
- `Step 2` は通過し、現在の blocker は install 不足ではなく、official codebase が `src/depth_anything_3` 配下であるのに `repo root` を `sys.path` へ入れていた点である
- 次段の `Colab` probe は `repo_root/src` を `sys.path` へ入れる修正版 `Step 3` で import check をやり直す
- `Step 3` 再試行では `src_root`、`plyfile`、`trimesh` の blocker を越え、`depth_anything_3.api` import は通過した
- `Step 4` では T4 上で core 推論自体は通過し、現在の blocker は `prediction.conf` を必須扱いした保存処理が `None` で落ちる点である
- `HF_TOKEN` warning は public model download では optional であり、現段階の blocker ではない
- `conf` / `intrinsics` / `extrinsics` を optional 扱いへ修正した結果、`2026-03-29` に T4 上で `1 frame` 推論は end-to-end で完了した
- 現在の次段は、`MRL-7` として `10s` 前後の整った実動画を使う `multi-frame` densify と、`PLY` viewer でぼんやり見える再現モデルを確認することである
- `gsplat` warning は出るが、これは `3DGS rendering` 用の optional dependency であり、現段階の `DA3Metric-Large` metric depth bootstrap の blocker ではない
- ここからは blank restart に戻さず、同じ runtime で blocker を 1 件ずつ解消しながら bootstrap 仕様へ反映する
- `DA3Metric-Large` の最適な package / module 構成、weight 配布元、download URL の返却方式は未決定である
- 人物 path の視覚再拘束に使う実データ条件が未確定である
- `ReviewArtifact` の最終 viewer 実装先は Android 固定ではない
- 取得元 app data の配置差分は実機ごとの差を吸収する必要がある
- multi-app 化では共通 source を維持しつつ app role を分ける必要がある
- `Colab` account 情報は未取得であり、remote 実行は後続 task とする
- `UX-only` 確認と本機能完成 gate を plan 上で分離していなかったことに加え、admin `UX check` 完了前に `i-pass` を付けていたため、closeout が過大になった

### 次の確認

1. `trajectreview-modeling` を `DA3Metric-Large` depth 推定 + `ARCore pose` / intrinsics 統合、multi-route 比較、採用 route 運用化の 3 段で閉じる
2. `trajectreview-reviewing` を `ReviewArtifact` 実 viewer と same-time highlight 操作まで閉じる
3. `MRL-7` で `10s` 前後の整った実動画から複数 frame を sampling し、world point cloud を統合して `PLY` で粗い再現モデルを確認する
4. その後に後続 `MRL-**` として request 起点 UX、`job_status.json`、waiting ring、download URL、reviewing viewer を順次切り出す

### 作業所有権

- Codex が `project-truth.md`、`ux-b2t-hypo.md`、admin test 関連文書の再開基線整備、`MRL` 再編整合作業、以後の `MRL` 継続作業を担当する

## BDD

### 目的文

この章は `prj-kisaragi_0002` の提供価値、`Purpose Story`、`System Behaviors`、`MRL` / `mRL` の対応を定義する。

### 目指す姿

- 利用者は、現場で記録した data を渡すだけで、次に何をすべきかを迷わず進められる
- 利用者は、空間の見え方、主カメラの動き、人物の動き、同じ時刻の位置関係を 1 つの review 文脈で確認できる
- 利用者は、成立しなかった処理を結果だけでなく理由付きで把握し、再取得や再実行の判断をすぐ行える
- 運営者は、入力補正、モデル生成、レビューを段階ごとに切り分けつつ、同じ session 契約のまま開発と運用を継続できる

### 提供方針

- 最適条件は 1 台の主カメラ動画、主カメラ側 `IMU`、人物側 `IMU`、および人物の映り込みである
- `GNSS` は任意入力とし、なくても `ARCore` 空間を基準に成立させる
- 主空間再構成は `DA3Metric-Large` と `ARCore pose` / intrinsics の統合を first target とする
- remote modeling は `Google Drive` と `Colab` を使う route を主経路とし、sampling / intrinsics handling を比較運用する
- 閲覧成果物は `3DGS` 系の空間表現、経路表示、同時刻ハイライト、`attention point` を一体で扱う
- まず受理、診断、実行可否を固め、その後に空間、経路、閲覧を段階分離して実装する

### Purpose Story
#### 利用者(user)
- `su1`: 利用者は、入力セッション folder を選択し、抽出結果をその場で得られる
- `su2`: 利用者は、抽出後に時刻整列とデータ確からしさを数値で確認できる
- `su3`: 利用者は、現場記録開始、停止、session 保存、診断前 export までを 1 つの入口で進められる
- `su4`: 利用者は、記録停止後に同じ入口で品質確認結果と修正指示を読める
- `su5`: 利用者は、品質確認を通した session を遠隔の保存場所へ転送できる
- `su6`: 利用者は、後段の空間再構成で使うカメラ校正情報と frame 対応情報を、記録時点で失わず残せる
- `su7`: 利用者は、必要な入力がそろっているかを受理時点で把握できる
- `su8`: 利用者は、人物の映り込みが十分かどうかを、不足入力や品質低下とあわせて診断で読める
- `su9`: 利用者は、空間再構成と人物経路再構成に必要な条件を満たした時だけ `処理を開始` を受け取れる
- `su10`: 利用者は、実行中に今どの段階を処理しているかを、思考コスト最小で把握できる
- `su11`: 利用者は、空間再構成が成立しにくそうな時に、データの再取得を検討できる
- `su12`: 利用者は、スマホまたは PC から model 生成 request を起点にし、対象 data directory を指定して処理を開始できる
- `su13`: 利用者は、待ち時間に waiting ring と現在処理段階を見ながら、そのまま完了を待てる
- `su14`: 利用者は、処理完了後に生成 data の download URL を受け取り、次の確認へ進める
- `su15`: 利用者は、主空間の見え方と主カメラ経路を確認できる
- `su16`: 利用者は、人物の動きが主空間へ同じ時刻で重ねられた結果を確認できる
- `su17`: 利用者は、見失い区間と再拘束の不確実性を理由付きで把握できる
- `su18`: 利用者は、同じ時刻の位置関係をハイライトし、注視すべき区間を絞り込める
- `su19`: 利用者は、生成済みの閲覧成果物を操作し、空間と経路をレビューできる
#### 運営者(developer)
- `sd1`: 運営者は、4 分担の境界と出力契約だけで開発と運用を継続できる
- `sd2`: 運営者は、抽出 bundle を見れば raw と `trajectreview` 派生出力の境界を追える
- `sd3`: 運営者は、抽出直後の bundle だけで `SpaceReconstruction` 着手可否と blocker を判断できる
- `sd4`: 運営者は、入力補正、モデル生成、レビュー操作を app 単位で分けて実行できる
- `sd5`: 運営者は、統合 app からも同じ workflow を通しで扱え、手戻り時にどの app 範囲で問題が起きたかを即座に切り分けられる
- `sd6`: 運営者は、4 app の各画面で mock ではなく直近の実 bundle を読み、同じ project truth で UX 確認できる
- `sd7`: 運営者は、`trajectreview-modeling` から request 起点の local sample と handoff request を生成し、PC 上で logic を先に検証できる
- `sd8`: 運営者は、指定した `Google Drive` directory を `Colab` 側が読み、実行状態と result URL を返す contract を維持できる
- `sd9`: 運営者は、`trajectreview-modeling` だけで `DA3Metric-Large` の metric depth 推定、`ARCore pose` / intrinsics 統合、`3DGS` 系主空間モデル生成の成否を確認でき、必要になった時は複数 route 比較へ広げられる
- `sd10`: 運営者は、比較結果から暫定採用 route を決め、以後の既定 route と research route を分けて運用できる
- `sd11`: 運営者は、`UX-only` 確認、契約固定、local sample、本機能完成を別 gate として追跡できる

### System Behaviors
#### 利用者起点
- `bu1`: `InputPackaging` app は入力セッション folder またはその 1 段上の parent directory を選択し、`session_manifest.json` / `manifest.json`、`video_frame_timestamps.csv` / `frames.csv`、`imu.csv`、`bt.jsonl` / `ble_scan.jsonl` / `bt_events.csv` / `bt.csv`、`poses.jsonl` / `arcore_pose.jsonl` / `arcore_pose.csv` を読める
- `bu2`: extractor は raw file を `isensorium/`、派生 file を `trajectreview/` に分離して app export dir へ出力する
- `bu3`: extractor は `sensor_quality.json` に時刻整列 delta、completeness score、pose coverage ratio を含める
- `bu4`: Android UI は抽出元、抽出先、`ready_for_diagnose`、欠落入力、主要 quality 数値を 1 画面で返す
- `bu5`: `trajectreview-correcting` は現場記録開始、停止、session 保存、input export を app 内で完結し、後段が読む concrete bundle を生成する
- `bu6`: `trajectreview-correcting` は最新 session を再読込し、`data-check` により readiness、quality、blocker、recommended correction を返す
- `bu7`: `trajectreview-correcting` は保存済み session 一覧を表示し、取得日時と長さを確認でき、既存 session を選択して再転送または rename できる
- `bu8`: `trajectreview-correcting` は `data-check` 済みの session を選び、送信する data group を選んだうえで、`Storage Access Framework` を通じて選択された `Google Drive` 保存場所へ zip 転送する
- `bu9`: `trajectreview-correcting` は `Storage Access Framework` で選ばれた `Google Drive` 保存場所に対して、選択 session 数に応じた zip を作成して同期できる
- `bu10`: `trajectreview-correcting` は `ARCore Session.update()` で得た同一 frame から pose、frame timestamp、capture timestamp、image intrinsics、texture intrinsics、lens distortion、tracking state を 1 record として保存し、`camera_calibration_summary.json` と `frame_pose_index.csv`、`images/` を派生出力する
- `bu11`: 受理時に、主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意 `poses` / `gnss` の充足状況を `SessionPackage` へ要約する
- `bu12`: `Diagnose` は、人物映り込みの十分性、不足入力、品質低下、修正理由を `Thin Status` で返す
- `bu13`: 実行可否 gate は、主カメラ動画、主カメラ `IMU`、人物側 `IMU`、空間再構成前提、経路再構成前提の readiness を満たした時だけ `処理を開始` を返す
- `bu14`: 実行 phase は、`Next Action` を常に `完了を待つ` 1 件に保ち、waiting ring と現在段階を別 line で返す
- `bu15`: `DA3Metric-Large` の入力成立が難しい時は、remote modeling を開始せず `入力条件を見直す` を返す
- `bu16`: `trajectreview-modeling` は、スマホまたは PC からの request を受け、`Google Drive` 上の入力 directory と result directory を指定した `Colab` 実行 request を export する
- `bu17`: `trajectreview-modeling` は、remote 実行中の状態を polling し、waiting ring、現在段階、直近更新時刻を request 元画面へ返す
- `bu18`: `trajectreview-modeling` は、remote 実行完了後に `Colab` 側 download URL と result summary を返し、受理後に `SpacePackage`、`TrajectoryPackage`、`modeling_handoff_manifest.json` を更新する
- `bu19`: `SpacePackage` は、`DA3Metric-Large` の metric depth と `ARCore pose` / intrinsics による world projection から得た主空間基準、主カメラ path、空間品質、および review 側が消費できる `gs_model` を返す
- `bu20`: `TrajectoryPackage` は、主カメラ path、人物 path、不確実性、再拘束点を同じ `Timeline` 上で返す
- `bu21`: 人物 path の relink は visual match confidence、time gap、anchor proximity、`BT` 主体維持、`IMU` 連続性で判定し、不成立時は不確実性を上げる
- `bu22`: `Verify` は空間品質と経路品質を同時に返し、`Interpret` は同時刻ハイライト候補と `attention point` を返す
- `bu23`: `trajectreview-reviewing` は `ReviewArtifact` 実体を読み、viewer 操作、same-time highlight、`attention point` jump を返す
- `bu24`: `Assembly` は `3DGS` 系空間表現の操作情報、経路、同時刻ハイライト情報を束ねた `ReviewArtifact` を唯一生成する

#### 運営者起点
- `bd1`: parser は `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を受理する
- `bd2`: `trajectreview` の docs、build、test、生成物経路は `prj-kisaragi_0002` 配下で完結し、要約と生の生成物を分離する
- `bd3`: `InputPackaging` は取得元 raw に加えて、`input_readiness.json`、`sensor_quality.json`、`frame_pose_index.csv`、`member_identity_map.json` を分担インターフェースとして出力する
- `bd4`: 4 分担の各段階は、前段の出力契約だけを読めば次段へ着手できる
- `bd5`: extractor は `video.mp4` と `video_events.jsonl` を含む raw bundle を維持し、後段が主カメラ動画を再利用できる
- `bd6`: extractor は `session_package.json` に source file、timebase、stream count、quality 指標、required / optional input を正規化して出力する
- `bd7`: extractor は `space_handoff_manifest.json` に `ready_for_space_reconstruction`、blocker、利用 artifact、次 action を出力する
- `bd8`: Android UI は `ready_for_space_reconstruction` と blocker を抽出結果画面で返す
- `bd9`: Android project は `trajectreview-correcting`、`trajectreview-modeling`、`trajectreview-reviewing`、統合 app の 4 app module を持ち、共通 source を再利用する
- `bd10`: `trajectreview-correcting` は現場記録、intake / diagnose / correction に必要な画面と文言だけを主表示にする
- `bd11`: `trajectreview-modeling` は `SpaceReconstruction` と `TrajectoryReconstruction` に必要な request 起点、進行表示、result 受け渡しを主表示にする
- `bd12`: `trajectreview-reviewing` は verify / review / same-time highlight を主表示にし、統合 app は全 workflow を束ねる
- `bd13`: correcting、modeling、reviewing、統合 app は、選択した実 bundle から `ReviewContractSnapshot` を再構成し、mock 固定状態に依存しない
- `bd14`: `trajectreview-modeling` は `session_package.json`、`sensor_quality.json`、`space_handoff_manifest.json`、`camera_calibration_summary.json` を読み、`local_model_summary.json`、`colab_job_request.json`、`job_status.json`、`review_artifact_stub.json` を生成する。これは `Colab` 実行前の request preflight と handoff 準備を担う
- `bd15`: `trajectreview-reviewing` と統合 app は `local_model_summary.json` と `review_artifact_stub.json` を読んで verify / review 状態を組み立てる
- `bd16`: `trajectreview-modeling` は、指定した `Google Drive` directory から zip または `session_root/` を正規化して読み、`Colab` runtime、status 更新、result URL 公開先を再現可能に構築できる
- `bd17`: `trajectreview-modeling` は `session_package.json`、`arcore_pose.jsonl`、`frame_pose_index.csv`、`camera_calibration_summary.json`、frame 群から `DA3Metric-Large` 用の前処理入力、metric depth 推定、world projection、`3DGS` 系主空間モデル生成を route 単位で実行できる
- `bd18`: `trajectreview-modeling` は、まず `10s` 前後の整った実動画から `multi-frame` densify を行い、主空間の見え方と主カメラ path を粗くでも把握できる再現モデルを返せる。route 比較が必要になった時は、sampling route、intrinsics route、ごとの quality、runtime、resource usage、failure reason を `benchmark_summary.json` へ集約できる
- `bd19`: `trajectreview-modeling` は比較結果から `selected_route.json` を生成し、採用 route と research route を分離できる
- `bd20`: `MRL` / `mRL` の `i-pass` は admin `UX check 完了` と本来機能の実行証跡を要件とし、`UX-only`、contract、sample、build / install は補助 gate として別記する



### 受け入れ基準
| story-id | behavior-id | 観点 | 受け入れ基準 |
| --- | --- | --- | --- |
| `su1` | `bu1`,`bu2`,<br>`bu4` | app 抽出 | `trajectreview` から入力セッション folder を選択し、抽出 bundle を生成できる |
| `su2` | `bu3`,`bu4`,<br>`bd3` | quality 数値 | 時刻整列 delta、completeness score、pose coverage ratio、欠落入力が抽出直後に確認できる |
| `su3` | `bu5` | correcting 本機能 | `trajectreview-correcting` だけで現場記録開始、停止、session 保存、input export まで進められる |
| `su4` | `bu6` | correcting data-check | `trajectreview-correcting` が同じ app 内で `data-check` 結果、blocker、recommended correction を返す |
| `su5` | `bu7`,`bu8`,<br>`bu9` | Google Drive transfer | `trajectreview-correcting` が `data-check` 済み session を 1 件以上選び、`送信Dataset` popup と data 一覧 popup を使って転送対象を確定し、懸念がある data を `▲` 表示したうえで、選択した `Google Drive` 保存場所へ zip を保存できる |
| `su6` | `bu10` | `DA3` 前段 calibration | `trajectreview-correcting` が `ARCore` frame ごとの camera intrinsics、texture intrinsics、lens distortion、frame timestamp を保存し、後段 `DA3 MetricLarge` へ渡せる |
| `su7` | `bu11`,`bd1`,<br>`bd3` | 受理契約 | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意 `poses` / `gnss`、追加出力の有無が 1 つの要約として読める |
| `su8` | `bu12` | diagnose UX | 人物映り込みの十分性、不足入力、品質低下、修正理由が `Thin Status` で読める |
| `su9` | `bu13` | 実行可否 gate | readiness 未達時は `処理を開始` を返さず、修正 action を返す |
| `su10` | `bu14` | 実行 UX | `Next Action` は常に 1 件で、waiting ring と現在段階は補足 line に分離される |
| `su11` | `bu15` | パイプライン安全性 | 主空間再構成 failure 時に remote modeling を開始せず、入力見直し理由を返す |
| `su12` | `bu16` | modeling request 起点 | `trajectreview-modeling` がスマホまたは PC 起点で入力 directory と result directory を指定した remote 実行 request を作成できる |
| `su13` | `bu14`,`bu17` | waiting UX | waiting ring が回り続け、現在段階と直近更新時刻が request 元画面で読める |
| `su14` | `bu18` | result download 導線 | 処理完了時に download URL と result summary が表示され、次段へ進める |
| `su15` | `bu19` | 主空間確認 | 主空間基準、主カメラ path、空間品質が読める |
| `su16` | `bu20`,`bu21` | 人物経路確認 | 人物 path が主空間へ重ねられ、不確実区間と再拘束点が識別できる |
| `su17` | `bu21` | 不確実性 | 再拘束失敗時に不確実性 mode と理由が更新される |
| `su18` | `bu22` | ハイライト | 同じ時刻の位置関係と `attention point` に時間範囲と理由が入る |
| `su19` | `bu23`,`bu24` | 閲覧成果物 | `ReviewArtifact` を開き、`3DGS` 操作、経路表示、同時刻ハイライトを操作できる |
| `sd1` | `bd2`,`bd3`,<br>`bd4` | 独立運用 | docs / build / test が project 内で完結し、段階間契約だけで分担着手できる |
| `sd2` | `bu2`,`bd2` | bundle 境界 | `isensorium/` と `trajectreview/` が分離され、raw と派生出力を誤読しない |
| `sd3` | `bd5`,`bd6`,<br>`bd7`,`bd8` | 後段 handoff | `video.mp4` を含む raw bundle と `session_package.json` / `space_handoff_manifest.json` だけで `SpaceReconstruction` 着手可否と blocker を判断できる |
| `sd4` | `bd9`,`bd10`,<br>`bd11`,`bd12` | 作業分割 | 補正、モデル生成、レビュー操作を app 単位で分け、各 app が担当段階を明示できる |
| `sd5` | `bd9`,`bd12` | 統合運用 | 統合 app からも同じ workflow を通しで扱え、問題発生時に app 単位で切り分けられる |
| `sd6` | `bd13`,`bd15` | 実データ UX | 各 app が抽出済みまたは modeling 済み bundle を読み、直近実データに基づく状態を表示できる |
| `sd7` | `bd14`,`bd15` | request preflight | `Colab` account 未取得でも local sample model、request payload、reviewing 用 stub を生成し、PC 上で logic を先に検証できる |
| `sd8` | `bd16` | remote 実行運用 | `Google Drive` directory 指定、`Colab` bootstrap、status 更新、result URL 公開先の contract を維持できる |
| `sd9` | `bd17`,`bd18` | `DA3` modeling 確認 | まず `10s` 前後の整った実動画から `multi-frame` densify を行い、主空間の見え方と主カメラ path を粗くでも把握できる再現モデルを得られる。必要になった時は route 比較へ広げられる |
| `sd10` | `bd18`,`bd19` | route 運用化 | 採用 route と research route が分離され、既定 route を machine-readable に固定できる |
| `sd11` | `bd20` | gate 運用 | `UX-only`、contract、sample、本機能完成が別 gate として記録され、完了誤認が起きない |

## TDD
### 目的文
この章は `prj-kisaragi_0002` の BDD `System Behaviors` を、1 task 1 責務で実装と検証へ落とす。

### TDD タスク
| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `tu1` | `bu1` | session source alias intake | `manifest.json`、`frames.csv`、`bt.csv` を含む legacy alias と、1 段上 parent directory 選択を 1 抽出器で読める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `tu2` | `bu2` | raw / derived export bundle | app 抽出が `isensorium/` と `trajectreview/` を分離した bundle を出力する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt` |
| `tu3` | `bu3` | quality 指標 export | `sensor_quality.json` に時刻整列 delta、completeness score、pose coverage ratio が入る | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt` |
| `tu4` | `bu4` | extraction UI summary | Android UI が抽出元、抽出先、`ready_for_diagnose`、欠落入力、quality 数値を表示できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `tu5` | `bu5` | correcting end-to-end recording export | `trajectreview-correcting` で現場記録開始、停止、session 保存、input export までを 1 app 内で完了できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `tu6` | `bu6` | correcting data-check service | 最新 session から `sensor_quality.json`、`session_package.json`、`space_handoff_manifest.json`、recommended correction を生成できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/CorrectingDataCheckService.kt` |
| `tu7` | `bu6` | correcting data-check UI | 記録停止後に app 内で readiness、quality、blocker、recommended correction を確認できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/res/layout/activity_main.xml` |
| `tu8` | `bu7` | correcting stored session manager | 保存済み session 一覧に取得日時と長さが出て、selected session の再転送と rename ができる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `tu9` | `bu8` | correcting Drive transfer gate | `data-check` 済み artifact を持つ selected session が 1 件以上あり、かつ転送先が選択済みなら `転送実行` を許可し、画面直下のコメントで設定済み / 未設定を示せる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `tu10` | `bu8`,`bu9` | Google Drive zip transfer | selected `Google Drive` 保存場所へ、1 件選択時は `<session_id>.zip`、複数件選択時は複数 session を含む zip を作成し、選択した data group だけを zip に含めて保存できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `tu11` | `bu9` | SAF transfer contract | `CreateDocument` で選んだ `Google Drive` 保存場所へ write でき、転送先状態を app 内で設定済み / 未設定として確認できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `tu12` | `bu10` | correcting camera calibration capture | `ARCore` record に `sessionId`、`recordIndex`、`captureTimestampNs`、nested `pose` / `imageIntrinsics` / `textureIntrinsics` / `lensDistortion` を含め、`camera_calibration_summary.json` と `frame_pose_index.csv` を生成できる。`images/` は転送で要求された時だけ生成する | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/RecordingCoordinator.kt` |
| `tu13` | `bu10`,`bd20` | correcting calibration diagnostic separation | `camera_calibration_summary.json` が `読取試行あり成功 0 件`、`calibration export 実装前 data の可能性`、`coverage 低下` を区別して示せる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/CorrectingDataCheckService.kt` |
| `tu14` | `bu10`,`bd20` | shared camera intrinsics acquisition | `corecamera_shared_camera_trial` route の `arcore_pose.jsonl` で `captureDiagnostics.*.requested=true` が出て、intrinsics 未取得なら `request failure` として診断できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/CoreCameraTrialRuntime.kt` |
| `tu15` | `bu11` | `SessionPackage` intake summary | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意入力、時刻基準、品質状態を 1 summary に落とせる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `tu16` | `bu12` | `Thin Status` diagnose formatter | 人物映り込みの十分性、不足入力、品質、理由を `phase`、`pipeline`、`data_health`、`quality`、`issues` で返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu17` | `bu13` | execute readiness gate | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、空間再構成前提、経路前提がそろわない限り `処理を開始` を返さない | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu18` | `bu14` | run phase waiting UX | run phase の `Next Action` が常に 1 件で、waiting ring と現在段階を別 line に出せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu19` | `bu15` | remote modeling safety gate | 入力成立が難しいとき remote modeling を開始しない | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu20` | `bu16` | remote modeling request manifest | `modeling` app が request 元、入力 directory、result directory、job parameter、status 取得先を machine-readable に出力できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `tu21` | `bu17` | waiting ring status sync | request 元画面が polling により waiting ring、現在段階、直近更新時刻を同期表示できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `tu22` | `bu18` | completion download URL import | remote modeling 完了後に download URL と result summary を返し、`SpacePackage`、`TrajectoryPackage`、`modeling_handoff_manifest.json` を更新できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `tu23` | `bu19` | `SpacePackage` coordinate contract | 主カメラ path と主空間基準を返し、`GNSS` がない時に主 `ARCore` local 空間を唯一基準として返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu24` | `bu20` | `TrajectoryPackage` timeline registration | 主カメラ path、人物 path、不確実性、再拘束点を同じ時刻軸で返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu25` | `bu21` | relink uncertainty classifier | visual match confidence、time gap、anchor proximity、`BT` 維持情報で不確実性を決める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu26` | `bu22` | verify quality summary | `space` と `trajectory` の quality、同時刻比較の弱点、weak area を同時に返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu27` | `bu22` | interpret attention point synthesis | `attention point` と同時刻ハイライトに時間範囲、理由、不確実区間情報を持たせる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu28` | `bu23` | review artifact viewer | `reviewing` app が実 `ReviewArtifact` を読み、viewer と timeline 操作を提供できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/reviewing/` |
| `tu29` | `bu24` | `ReviewArtifact` boundary contract | `Assembly` だけが `3DGS` 操作、経路表示、同時刻ハイライトを含む `ReviewArtifact` を生成する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `td1` | `bd1` | Python session parser alias compatibility | `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を 1 parser で読める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `td2` | `bd2` | independent project boundary scan | `prj-kisaragi_0002` products と docs が外部 project の shared 参照なしで継続できる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py` |
| `td3` | `bd2` | output routing hygiene | Android build cache と raw test report が `--exsams`、summary が `--testlogs` に分離される | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/scripts/run_android_unit_tests.ps1` |
| `td4` | `bd3` | `InputPackaging` interface manifest | 取得元 raw に加え、受理判定、品質、frame-pose 対応、主体対応表が JSON と CSV の契約で出力される | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `td5` | `bd4` | stage handoff contract | 4 分担の各段階で入力、出力、受け渡し条件が文書と実装の両方で読める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py` |
| `td6` | `bd5` | video raw bundle export | app 抽出が `video.mp4` と `video_events.jsonl` を raw bundle に保持する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt` |
| `td7` | `bd6`,`bd7` | normalized handoff payload | Python parser と Android extractor が `session_package.json` と `space_handoff_manifest.json` を同じ契約で生成する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `td8` | `bd8` | space reconstruction gate summary UI | Android UI が `ready_for_space_reconstruction` と blocker を結果画面で返す | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `td9` | `bd9` | multi-app module build | `correcting`、`modeling`、`reviewing`、統合 app の 4 module が同じ repository で build できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/settings.gradle.kts` |
| `td10` | `bd10`,`bd11`,`bd12` | role-specific workflow filter | 各 app が自分の役割に対応する workflow 範囲と文言だけを主表示にする | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `td11` | `bd12` | integrated app overview | 統合 app が 3 app の担当境界を俯瞰表示し、切り分け理由を示せる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `td12` | `bd13` | extracted bundle snapshot loader | app が `session_package.json`、`sensor_quality.json`、`space_handoff_manifest.json`、`member_identity_map.json` を読んで実データ state を再構成できる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/WorkflowBundleServiceTest.kt` |
| `td13` | `bd14` | request preflight output | `modeling` app が `local_model_summary.json`、`colab_job_request.json`、`job_status.json`、`review_artifact_stub.json` を生成できる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/LocalModelingServiceTest.kt` |
| `td14` | `bd16` | drive directory bootstrap intake | `Colab bootstrap package` が指定した `Google Drive` directory から zip または `session_root/` を正規化して読める | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td15` | `bd16` | remote status and result locator | `job_status.json` に stage、updated_at、result availability、download URL を正規化できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td16` | `bd17` | `DA3Metric-Large` input manifest | `modeling` app が frame sampling、intrinsics mode、projection option を route 単位で `experiment_manifest.json` と `da3_input_manifest.json` に出力できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `td17` | `bd17` | metric depth and space runner | `DA3Metric-Large` の少なくとも 1 route を `Colab` で実行し、depth、world projection、`3DGS` 系主空間モデル生成に必要な出力を保存できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td18` | `bd17` | space reconstruction report | `metric scale confidence`、`depth continuity`、`point count estimate`、`gs_model` 生成結果、failure reason を `depth_estimation_report.json` と `space_quality.json` に正規化できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td19` | `bd18` | multi-frame densify visible reconstruction | `10s` 前後の整った実動画から複数 frame を sampling し、world point cloud を統合して、`PLY` viewer で粗くでも主空間の見え方と主カメラ path の対応を確認できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td20` | `bd18` | intrinsics route benchmark aggregation | 少なくとも 2 つの intrinsics / projection route の結果を同一比較表へ集約できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td21` | `bd19` | selected route decision artifact | 暫定採用 route、不採用理由、research route、再評価条件を `selected_route.json` に保存できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `td22` | `bd15` | reviewing actual bundle state | `reviewing` app と統合 app が modeling 結果を読み、verify / review 状態へ反映できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `td23` | `bd20` | gate classification rule trace | `UX-only`、contract、sample、本機能の区別が `ux-b2t-hypo.md`、`admin-mrl-test-method.md`、`admin-mrl-test-evidence.md` で矛盾なく追える | ready | `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/` |

### 実行方針
- `MRL-1` では `tu1` から `tu7`、`tu12`、`tu13`、`tu14` で `correcting` の記録、`data-check`、calibration 診断を固める
- `MRL-2` では `tu8` から `tu11` と `td6` から `td8` で `correcting` の転送、raw video 維持、handoff bundle を固める
- `MRL-3` では `td13`、`tu20` と runbook 実行で `modeling` の bootstrap / install 導線を固める
- `MRL-4` では `td12`、`td14`、`tu18`、`tu21`、`td23` で `modeling` の実 bundle 読込、request preflight、directory intake を固める
- `MRL-5` では `td16` から `td18` と `tu22`、`tu23` で `modeling` の single-frame `3DGS` smoke を固める
- `MRL-6` では evidence bundle の取得、download、local 参照導線を固定する
- `MRL-7` では `td19` を中心に `modeling` の `multi-frame` densify を固める
- 後続 `MRL-**` では `reviewing`、`system統合`、request / status UX、route 比較、採用 route 固定を、admin が手を動かす実態に合わせて順次切り出す
- 後続の利用者向け `MRL-**` では route 比較、採用 route 固定、request / status UX、remote result 返却、reviewing viewer、正式統合を、admin が手を動かす modeling 実態に合わせて順次切り出す

### 現在の見立て
- `tu1` から `tu7` と `td1` から `td8` の基礎 task は、契約実装、project 境界 scan、output routing 実行で `p-done` になった
- Python unittest、Android unit test、PowerShell script 実行により、入口契約から成果物 routing までの計画範囲を固定した
- 旧 `MRL-1` から `MRL-14` には、phase と手段と補助確認が混在していたため、現在は `correcting`、`modeling`、`reviewing`、`system統合` の各 phase に複数 `MRL` を割り当てる
- `MRL-1` と `MRL-2` は `correcting` phase の gate とし、実データ取得、`data-check`、`Google Drive` 転送、`SpaceReconstruction` handoff bundle までの admin evidence がそろったため、この段では `p-done` とする
- `td9` 以降の modeling / reviewing task は、基礎は通っているが本機能 close には未達である
- `MRL-3` から `MRL-6` は `modeling` phase のうち、bootstrap / install、実 bundle 読込、single-frame `3DGS` smoke、artifact 取得がそろった範囲として `p-done` とする
- `MRL-2` の転送 close 導線は、`現場撮影データ保存 -> data-check -> Google Drive転送 -> handoff bundle` を 1 app UX として閉じる。転送 block 内の順番と popup UX を正本に固定する
- `MRL-2` の事前設定は `転送先を選択 -> URL を確認または変更 -> 保存先fileを設定する -> Google Drive 上で保存先 file を選ぶ` を既定導線とし、既定 URL は `u/2` の指定 folder に固定する
- `td9` から `td23` と `tu20` から `tu29` は multi-app 骨格、実 bundle summary、request preflight、remote status、route 比較、viewer 検証としては有効だが、本機能完成の証拠としては不十分である
- `MRL-5` は、`correcting` 実データを使った single-frame `3DGS` 系主空間モデル候補の smoke 生成と生成 artifact 取得までを根拠に `p-done` とする
- `MRL-6` は、notebook evidence と local downloaded artifact bundle を product 側 evidence として取得できる段までを `p-done` とする
- 次段は `MRL-7` とし、`10s` 前後の整った実動画から `multi-frame` depth / world projection を積み上げて、admin が `PLY` viewer でぼんやり見える再現モデルを確認できる水準を first target に置く
- `MRL-**` は後続残件群として置き、task 実測で課題の大小が見えた時点で `MRL` / `mRL` の切り方を調整する
- 後続 `MRL-**` では、少なくとも `multi-route` 比較、`selected_route.json` 固定、request 起点 UX、`job_status.json` と waiting ring、download URL を含む result 返却、`SpacePackage` / `TrajectoryPackage` / `ReviewArtifact` handoff、reviewing viewer 実装、主空間 / 主カメラ経路 / 人物経路 / same-time highlight を同じ review 文脈で扱う統合 UX を順に残す
- modeling は admin の手作業を含むため、後続 `MRL` の達成基準は都度「いま実際に進めやすい粒度」へ合わせて更新する
- ただし `MRL` の達成品質として求める UX 自体は薄めず、元の north star である「利用者が主空間の見え方と主カメラ経路を確認できる」「処理状態と次 action を迷わず把握できる」方向に沿って各段の到達像を明記する

## `MRL` 対応表
- `MRL` は `BDD` の story / behavior と `TDD` の task を束ね、admin がどの gate test 項目を `UX check` すべきかを定義する。
- 各 row は「この gate で何を確認するか」を 1 つの test 項目として持ち、`task-id` が空でない限り、下の `TDD` と追跡可能でなければならない。
- `admin UX確認手順` は [admin-mrl-test-method.md](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-method.md) の章名または操作手順番号をそのまま書く。
- `admin evidence` は [admin-mrl-test-evidence.md](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md) の章名をそのまま書く。
- `現在 gate` と `UX評価状態` は `ready`、`active`、`p-done`、`i-pass` の 4 値だけを使う。
- `ready` は、未着手または開始待ちを示す。`UX評価状態` では、まだ admin `UX check` に出す段階ではないことを示す。
- `active` は、実装、検証、評価の進行中を示す。`UX評価状態` では、manual、実行環境、対象機能がそろい、admin が今すぐ test できるか test を進行中であることを示す。
- `p-done` は、当該 phase 範囲で成立確認済みを示す。`UX評価状態` では、phase 単位の UX 確認が一通り完了した状態を示す。
- `i-pass` は、関連統合範囲まで成立確認済みを示す。`UX評価状態` では、関連統合範囲まで含む admin `UX check` が完了し、結果が `admin-mrl-test-evidence.md` に記録済みであることを示す。
- `未収載` は、まだ `admin-mrl-test-method.md` に具体手順が無いことを明示する。

### 利用者主導 gate
| MRL | mRL | gate test 項目 | story-id | behavior-id | task-id | 現在 gate | UX評価状態 | admin UX確認手順 | admin evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MRL-1` | `-` | `trajectreview-correcting` で<br>現場記録、受理、診断、<br>calibration 診断までを<br>1 app UX として成立させる | `su1`,`su2`,<br>`su3`,`su4`,<br>`su6` | `bu1`,`bu2`,<br>`bu3`,`bu4`,<br>`bu5`,`bu6`,<br>`bu10` | `tu1`,`tu2`,<br>`tu3`,`tu4`,<br>`tu5`,`tu6`,<br>`tu7`,`tu12`,<br>`tu13`,`tu14` | `p-done` | `p-done` | 操作手順 1-8<br>p-done / i-pass の判断<br>fail の判断 | correcting batch 定義,<br>2026-03-29 correcting batch MRL-1 と MRL-2 close evidence |
| `MRL-1` | `mRL-1.1` | session source 読込、raw / derived 分離 export、現場記録から export までの一連実行を確認する | `su1`,`su3`,<br>`sd2` | `bu1`,`bu2`,<br>`bu5` | `tu1`,`tu2`,<br>`tu5` | `p-done` | `p-done` | 操作手順 1-8 | 2026-03-25 MRL-2 candidate evidence,<br>2026-03-29 correcting batch MRL-1 と MRL-2 close evidence |
| `MRL-1` | `mRL-1.2` | quality 数値表示、`data-check` artifact、recommended correction を確認する | `su2`,`su4` | `bu3`,`bu4`,<br>`bu6` | `tu3`,`tu4`,<br>`tu6`,`tu7`,<br>`tu12` | `p-done` | `p-done` | 操作手順 7-8 | 2026-03-26 MRL-2 candidate evidence,<br>2026-03-29 correcting batch MRL-1 と MRL-2 close evidence |
| `MRL-1` | `mRL-1.3` | calibration capture 診断の切り分けと shared camera route の intrinsics 実収集を確認する | `su6` | `bu10` | `tu13`,`tu14` | `p-done` | `p-done` | 操作手順 11-15,<br>p-done / i-pass の判断 | 2026-03-28 calibration diagnostic candidate evidence,<br>2026-03-29 correcting batch MRL-1 と MRL-2 close evidence |
| `MRL-2` | `-` | `trajectreview-correcting` で<br>`Google Drive` 転送と<br>`SpaceReconstruction` handoff bundle<br>生成までを成立させる | `su3`,`su5`,<br>`sd3`,`sd11` | `bu5`,`bu7`,<br>`bu8`,`bu9`,<br>`bd5`,`bd6`,<br>`bd7`,`bd8`,<br>`bd20` | `tu5`,`tu8`,<br>`tu9`,`tu10`,<br>`tu11`,`td6`,<br>`td7`,`td8` | `p-done` | `p-done` | 操作手順 8-15<br>p-done / i-pass の判断<br>fail の判断 | correcting batch 定義,<br>2026-03-29 correcting batch MRL-1 と MRL-2 close evidence |
| `MRL-2` | `mRL-2.1` | `1 回以上 data-check` 後の転送 gate と `Google Drive` 転送を確認する | `su5` | `bu7`,`bu8` | `tu8`,`tu9`,<br>`tu10` | `p-done` | `p-done` | 操作手順 8-13 | 2026-03-27 MRL-3 candidate evidence,<br>2026-03-29 correcting batch MRL-1 と MRL-2 close evidence |
| `MRL-2` | `mRL-2.2` | Drive folder 同期 contract と zip 転送結果を確認する | `su5`,`sd11` | `bu9`,`bd20` | `tu11` | `p-done` | `p-done` | 操作手順 10-13 | 2026-03-27 MRL-3 candidate evidence,<br>2026-03-29 correcting batch MRL-1 と MRL-2 close evidence |
| `MRL-2` | `mRL-2.3` | raw video を含む<br>`SessionPackage` と<br>`space_handoff_manifest` により<br>`SpaceReconstruction` handoff を確認する | `sd3`,`su3` | `bd5`,`bd6`,<br>`bd7`,`bd8`,<br>`bu5` | `td6`,`td7`,<br>`td8`,`tu5` | `p-done` | `p-done` | modeling batch<br>前提確認 1-4 | 2026-03-25 MRL-3 candidate evidence,<br>2026-03-29 correcting batch MRL-1 と MRL-2 close evidence |
| `MRL-3` | `-` | `Colab` 実行前の<br>package / config / runbook 導線と<br>bootstrap / install を<br>たどれることを確認する | `sd7`,`su12` | `bd14`,`bu16` | `td13`,`tu20` | `p-done` | `p-done` | modeling batch<br>操作手順 4-6<br>da3_colab_<br>clean_bootstrap_<br>runbook.md | modeling batch 定義,<br>2026-03-29 modeling bootstrap candidate evidence |
| `MRL-3` | `mRL-3.1` | `Colab` 実行前の package / config / runbook 導線を手動でたどれることを確認する | `sd7`,`su12` | `bd14`,`bu16` | `td13`,`tu20` | `p-done` | `p-done` | modeling batch <br>操作手順 4-6 と<br>da3_colab_<br>clean_bootstrap_<br>runbook.md | 2026-03-29 modeling bootstrap candidate evidence |
| `MRL-4` | `-` | `trajectreview-modeling` で<br>実 bundle 読込、<br>request preflight、<br>`Google Drive` directory intake までを成立させる | `sd6`,`sd7`,<br>`sd8`,`su12`,<br>`sd11` | `bd13`,`bd14`,<br>`bd16`,`bu16`,<br>`bd20` | `td12`,`td13`,<br>`td14`,`tu20`,<br>`td23` | `p-done` | `p-done` | modeling batch<br>操作手順 1-9 | modeling batch 定義,<br>2026-03-29 modeling preflight close evidence |
| `MRL-4` | `mRL-4.1` | 実 bundle snapshot 読込と request preflight 生成を確認する | `sd6`,`sd7`,<br>`su12` | `bd13`,`bd14`,<br>`bu16` | `td12`,`td13`,<br>`tu20` | `p-done` | `p-done` | modeling batch<br>操作手順 1-6 | 2026-03-26 MRL-4 candidate evidence,<br>2026-03-29 modeling preflight close evidence |
| `MRL-4` | `mRL-4.2` | `Google Drive` directory<br>bootstrap を確認する | `sd8`,`su12` | `bd16`,`bu16` | `td14`,`tu20` | `p-done` | `p-done` | modeling batch<br>操作手順 7-9<br>runbook の<br>事前準備 / 準備確認 | 2026-03-29 modeling bootstrap candidate evidence,<br>2026-03-29 modeling preflight close evidence |
| `MRL-5` | `-` | `DA3Metric-Large` による<br>single-frame `3DGS` 系<br>主空間モデル生成 smoke を<br>成立させる | `su14`,`su15`,<br>`sd9`,`sd11` | `bd17`,`bu18`,<br>`bu19`,`bd20` | `td16`,`td17`,<br>`td18`,`tu22`,<br>`tu23`,`td23` | `p-done` | `p-done` | modeling batch<br>操作手順 13-18<br>p-done / i-pass の判断<br>fail の判断<br>runbook の <br>Candidate Bootstrap v1 | modeling batch 定義,<br>2026-03-29 MRL-5 3DGS smoke candidate evidence |
| `MRL-5` | `mRL-5.1` | `DA3` input manifest と route export を確認する | `sd9` | `bd17` | `td16` | `p-done` | `p-done` | modeling batch <br>操作手順 13-14 | 2026-03-29 MRL-5 3DGS smoke candidate evidence |
| `MRL-5` | `mRL-5.2` | `Colab` 上の metric depth と `3DGS` 系主空間モデル生成を確認する | `sd9`,`su14` | `bd17`,`bu18` | `td17`,`tu22` | `p-done` | `p-done` | modeling batch<br>操作手順 15-17 と<br>da3_colab_<br>clean_bootstrap_<br>runbook.md の<br>Candidate Bootstrap v1 | 2026-03-29 MRL-5 3DGS smoke candidate evidence |
| `MRL-5` | `mRL-5.3` | `depth_estimation_report.json`、`space_quality.json`、`gs_model` を含む主空間要約を確認する | `su15`,`sd9` | `bu19`,`bd17` | `tu23`,`td18` | `p-done` | `p-done` | 未収載 | 2026-03-29 MRL-5 3DGS smoke candidate evidence |
| `MRL-6` | `-` | `modeling` の smoke 生成物を<br>admin が notebook / local download で取得し、<br>product 側 evidence として<br>再参照できることを確認する | `su15`,`sd11` | `bu19`,`bd20` | `tu23`,`td23` | `p-done` | `p-done` | da3_colab_<br>clean_bootstrap_<br>runbook.md<br>の Candidate 拡張状況 | 2026-03-29 modeling evidence bundle close evidence |
| `MRL-6` | `mRL-6.1` | `Google Colab` 実行 notebook を product 側 evidence として保存し、再参照できることを確認する | `sd11` | `bd20` | `td23` | `p-done` | `p-done` | da3_colab_<br>clean_bootstrap_<br>runbook.md の<br>Candidate 拡張状況 | 2026-03-29 modeling evidence bundle close evidence |
| `MRL-6` | `mRL-6.2` | local downloaded smoke artifact 一式を product 側 evidence として保存し、再参照できることを確認する | `su15`,`sd11` | `bu19`,`bd20` | `tu23`,`td23` | `p-done` | `p-done` | da3_colab_<br>clean_bootstrap_<br>runbook.md の<br>Candidate 拡張状況 | 2026-03-29 modeling evidence bundle close evidence |
| `MRL-7` | `-` | `10s` 前後の整った実動画から<br>`multi-frame` で、利用者が<br>主空間の見え方と主カメラ経路を<br>粗くでも把握できる再現モデルを得る | `sd9`,`su15`,<br>`sd11` | `bd18`,`bu19`,<br>`bd20` | `td19`,`td23` | `active` | `ready` | `未収載` | `未収載` |
| `MRL-7` | `mRL-7.1` | `10s` 前後の整った実動画から `multi-frame` sampling route を回し、`PLY` でぼんやり見える再現モデルと主カメラ path の対応を確認する | `sd9`,`su15` | `bd18`,`bu19` | `td19` | `active` | `ready` | `未収載` | `未収載` |
| `MRL-7` | `mRL-7.**` | 補助比較や追加確認が必要なら、実測に応じて `multi-frame` 内の追加確認を切り出す | `sd9`,`sd11` | `bd18`,`bd20` | `td19`,`td23` | `ready` | `ready` | `未収載` | `未収載` |

### 利用者向け後続 `MRL-**` に紐づく運営者補助 gate
| MRL | mRL | gate test 項目 | story-id | behavior-id | task-id | 現在 gate | UX評価状態 | admin UX確認手順 | admin evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MRL-**` | `-` | 利用者向け後続 `MRL-**` を支える<br>補助 gate として、route 比較、採用 route 固定、<br>request / status UX、reviewing viewer、正式統合を<br>実測に応じて順次切り出す | `sd6`,`sd9`,<br>`sd10`,`su19`,<br>`sd11` | `bd15`,`bd18`,<br>`bd19`,`bu23`,<br>`bu24`,`bd20` | `td20`,`td21`,<br>`td22`,`tu28`,<br>`tu29`,`td23` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.1` | `multi-route` 比較を行い、quality、runtime、resource usage、failure reason を同一 session 上で比較できる | `sd9`,`sd11` | `bd18`,`bd20` | `td20`,`td23` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.2` | 暫定採用 route を `selected_route.json` として固定し、research route と再評価条件を追える | `sd9` | `bd19` | `td21` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.3` | request 元から input directory、result directory、route id を束ねて remote 実行 request を作り、waiting ring と `job_status.json` を読み続けられる | `sd6`,`su10`,<br>`su13` | `bd15`,`bu14`,<br>`bu17` | `td22`,`tu28`,<br>`td23` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.4` | remote 完了後に download URL と result summary を返し、`SpacePackage`、`TrajectoryPackage`、`ReviewArtifact` handoff を後段へ渡せる | `sd10`,`su19` | `bu23`,`bu24` | `tu28`,`tu29` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.5` | reviewing viewer で主空間、主カメラ経路、人物経路、same-time highlight、`attention point` を同じ review 文脈で扱える | `su18`,`su19` | `bu22`,`bu24` | `tu27`,`tu29` | `ready` | `ready` | `未収載` | `未収載` |
