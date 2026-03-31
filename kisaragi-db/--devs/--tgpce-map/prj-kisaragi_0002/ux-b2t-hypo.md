# ux_b2t-hypo.md

## 文書の役割

この文書は `prj-kisaragi_0002` プロジェクトの goal、plan、current、evidenceを、1 つに統合した正本とする。

## current_state

### 現在の開発状況

| 項目 | 状況 |
| --- | --- |
| `correcting` | `MRL-1` と `MRL-2` の実装と証跡はそろっている。長時間収録では screen off は抑止済みで、`shared-camera` 動画化の `OutOfMemoryError` と停止時 finalize hang は修正済みである。admin 実機では `3分` 収録で停止成功まで確認できたため、残りは `MRL-2S` の `10min` 実収録確認である |
| `modeling` | `MRL-3` から `MRL-8` は `p-done` である。`MRL-7` は `mRL-7.1` と `mRL-7.2` が `p-done` になり、multi-frame point cloud から gaussian short optimization まで到達した。`MRL-8` では runbook 本体の前段に Drive input candidate scan / widget select を追加し、selected input を bootstrap 本体と `MRL-7` one-block の両方へ handoff できる状態を閉じた。運用形は notebook 全体の `Run all` ではなく、widget 選択を 1 回挟んでから残りを上から順に流す方式である。`MRL-9` は `da3-giant` の `inference()` に `infer_gs=True` を与え、`e3nn` install を import 前に置くことで `gs_ply`、`gs_video`、`scene.glb`、`exports/npz/results.npz` を `MyDrive/trajectreview/modeling/...` へ保存できる first route まで進んだ。次は external viewer で `gs_ply` を開く `mRL-9.2` である |
| `reviewing` | summary と stub 読込まではあるが、実 `ReviewArtifact` viewer と same-time highlight 操作は未実装である |

### 現在の blocker

| id | blocker | 影響 | 現在の扱い |
| --- | --- | --- | --- |
| `BLK-1` | `MRL-7` の範囲に `TraceCore` 最小表示、route 比較、viewer 後続論点が混在している | `MRL` closeout と `BDD` の焦点がぼける | `TraceCore` 最小表示だけを `MRL-7` の中心に寄せ、後続は `MRL-**` へ分離する |
| `BLK-2` | sampling / intrinsics の最終採用 route が未決定 | `modeling` の採用 route 固定が止まる | 比較基盤、比較実験、採用 route 運用化の 3 段で閉じる前提を維持する |
| `BLK-3` | 人物 path の視覚再拘束に必要な実データ条件が未確定 | `TrajectoryPackage` の安定化条件が読みにくい | `MRL-7` では最小表示を優先し、視覚再拘束条件は後続検証へ送る |
| `BLK-4` | `ReviewArtifact` の最終 viewer 実装先と same-time highlight 実装が未完 | `reviewing` の本機能 gate を閉じられない | 後続 `MRL-**` として分離して扱う |
| `BLK-5` | `UX-only`、contract、sample、本機能完成の gate が文書上で十分に分離されていない | closeout が過大になりやすい | `BDD` / `TDD` / `MRL` の再構成で gate 境界を明確にする |
| `BLK-6` | `correcting` の短中時間帯は `3分` 収録まで停止成功を確認したが、`10min` 連続収録はまだ未確認である | 現場記録の本機能成立を `i-pass` にできない | `MRL-2S` で `10min` 実収録を行い、screen off 抑止と finalize 完了を確認する |
| `BLK-7` | `DA3 Colab` runbook は Drive 上の特定 zip path を hardcode しており、任意 input を script だけで選んで本体へ渡せない | fresh runtime で入力を差し替えるたびに手編集が必要になり、bootstrap の再現性が落ちる | `MRL-8 p-done` により解消済み。Drive input candidate scan、widget select、selected input handoff を runbook 正本へ反映済み |
| `BLK-8` | `DA3 Giant` / `Giant Large` の `infer_gs=True` route は、`gs_ply` / `gs_video` を返せる前提があるが、現行 project は `DA3Metric-Large` 固定で contract 未整備である | `gs_ply` を正式 `gs_model` として扱う route と top camera viewer 拡張が止まる | `MRL-9` で `MetricLarge route` を rollback baseline に固定したまま、`Giant` Gaussian branch の実装 route を追加し、`gs_ply` / `gs_video` と viewer 導線を順に固める |

### 次の一手

1. `MRL-2S` で `correcting` の bounded stop 修正 build を `10min` 実収録で確認し、連続収録安定化を閉じる
2. `MRL-7` を `TraceCore` の最小表示に限定し、route 比較と viewer 後続論点を `MRL-**` へ切り分ける
3. `MRL-9` として、`DA3 Giant` / `Giant Large` の `infer_gs=True` route を実装し、`fps = 1`、`frames = 60`、`process_res = 504`、`chunk = 20` または `30` を first config に `gs_ply` / `gs_video` 出力と viewer 可視化を固める
4. 後続 `MRL-**` として、`gs_ply` を top camera renderer と reviewing viewer へ接続する route、multi-view / 長時間 optimization、request / status / result download UX を整理する
5. `reviewing` と admin `UX check` の後続 gate を整理し、`ux-b2t-hypo.md` と証跡文書の closeout 基準を揃える


## BDD

### 目的文

この章は `prj-kisaragi_0002` の提供価値、`Purpose Story`、`System Behaviors`、`MRL` / `mRL` の対応を定義する。

- `TraceCore` を `MRL-7` の最小成立像として扱い、何を見せれば review 価値が出るかを固定する。
- 最小構成で直接扱う価値と、後続 `MRL-**` へ送る価値を分けて扱い、開発負荷を抑えながら付加価値を高める。

### 利用者に提供するレビュー価値

| 見方 | 分かること |
| --- | --- |
| 全体俯瞰 | どの範囲を主に使っていたか |
| 時系列再生 | どの順で移動したか |
| camera と人の相対表示 | 撮影者と人の位置関係 |
| 滞留箇所の確認 | 長くいた場所、動きが集中した場所 |
| 軌跡の重なり確認 | 交錯、往復、無駄な動線の兆候 |

### 最終目標

- 最終目標は、作業後に manager が現場空間における人、作業機の時系列の関係を視覚で確認でき、実施した作業 process が判読できるようにすることである。
- ただし最小構成で直接扱うのは、現場空間の再現、移動軌跡、相対位置関係、時系列の把握である。
- 人がその場で具体的に何をしていたかの理解は、この最小構成の範囲外とする。
- 最終到達点は `10時間` 作業を一貫処理、一貫閲覧できることとし、当面は `1分` 程度の動画で成立させることを目標とする。

### 最小構成

- 利用者は、主空間、camera 軌跡、人軌跡を同じ時間軸で確認できる。
- 利用者は、全体俯瞰、時系列、相対表示として review 価値を感じられる。
- 利用者は、人の具体的作業内容まではまだ分からなくても、移動、位置関係、時系列は把握できる。
- 人の個体 `ID` は取らない。
- `3DGS` 上に camera 軌跡と映り込む人の軌跡が、安っぽく見えない見た目で表示される状態を成立条件とする。

| 項目 | 内容 |
| --- | --- |
| camera 動画 | 屋外、屋内作業者が断続的に映る |
| camera data | `ARCore` 相当の pose、camera parameter、時刻同期情報を取得できる |
| 取得頻度 | `5` から `10fps` 程度 |
| camera `IMU` | 動画撮影と同時取得できる |
| 人物側条件 | カメラに映り込む人は `IMU` 付き smartphone を保持している |
| 最適条件 | 1 台の主カメラ動画、主カメラ側 `IMU`、人物側 `IMU`、および人物の映り込みを前提にする |
| `GNSS` | 任意入力とし、なくても `ARCore` 空間を基準に成立させる |
| 移動速度 | 人、作業機とも `5km/h` 以下を最低限の実用前提とする |
| 初期対象 | `1分` 程度の動画 |
| 主空間再構成 | `DA3Metric-Large` と `ARCore pose` / intrinsics の統合を first target とする |
| remote modeling | `Google Drive` と `Colab` を使う route を主経路とし、sampling / intrinsics handling を比較運用する |
| 閲覧成果物 | `3DGS` 系の空間表現、経路表示、同時刻ハイライト、`attention point` を一体で扱う |
| 実装順 | まず受理、診断、実行可否を固め、その後に空間、経路、閲覧を段階分離して実装する |
| 空間理解 | 現場の見た目と位置関係が分かる |
| 動き理解 | camera と人がどう動いたか分かる |
| 相対理解 | 人と camera の関係が分かる |
| 時系列理解 | どの順で動いたか分かる |
| 信頼感 | 安っぽく見えず、確認に使える |

| 後回し項目 | 理由 |
| --- | --- |
| 人物個体 `ID` の確定 | 最小価値に必須ではない |
| 人物ごとの厳密再同定 | 初手で必要ない |
| 人の具体的作業内容の理解 | 背景と軌跡だけでは扱えない |
| 高度な `IMU` 融合 | 重く、初手に向かない |
| `10時間` 対応 | 最終目標だが初手ではない |
| 高度分析 `UI` | まずは見えることが先 |


### Purpose Story

| story-id | 区分 | 内容 |
| --- | --- | --- |
| `su1` | 利用者 | 入力セッション folder を選択し、抽出結果をその場で得られる |
| `su2` | 利用者 | 抽出後に時刻整列とデータ確からしさを数値で確認できる |
| `su3` | 利用者 | 現場記録開始、停止、session 保存、診断前 export までを 1 つの入口で進められる |
| `su4` | 利用者 | 記録停止後に同じ入口で品質確認結果と修正指示を読める |
| `su5` | 利用者 | 品質確認を通した session を遠隔の保存場所へ転送できる |
| `su6` | 利用者 | 後段の空間再構成で使うカメラ校正情報と<br>frame 対応情報を、記録時点で失わず残せる |
| `su6a` | 利用者 | `trajectreview-correcting` を前面表示したまま、screen off や自動減光で収録が落ちない状態で長時間記録できる |
| `su7` | 利用者 | 必要な入力がそろっているかを受理時点で把握できる |
| `su8` | 利用者 | 人物の映り込みが十分かどうかを、<br>不足入力や品質低下とあわせて診断で読める |
| `su9` | 利用者 | 空間再構成と人物経路再構成に必要な条件を満たした時だけ、<br>`処理を開始` を受け取れる |
| `su10` | 利用者 | 実行中に今どの段階を処理しているかを、思考コスト最小で把握できる |
| `su11` | 利用者 | 空間再構成が成立しにくそうな時に、データの再取得を検討できる |
| `su12` | 利用者 | スマホまたは PC から model 生成 request を起点にし、<br>対象 data directory を指定して処理を開始できる |
| `su13` | 利用者 | 待ち時間に waiting ring と現在処理段階を見ながら、そのまま完了を待てる |
| `su14` | 利用者 | 処理完了後に生成 data の download URL を受け取り、次の確認へ進める |
| `su15` | 利用者 | `TraceCore` 上で主空間、主カメラ経路、人軌跡を見比べ、<br>全体俯瞰、時系列、相対表示に加え、滞留や交錯の兆候も確認できる |
| `su16` | 利用者 | 人物の動きが個体 `ID` なしでも主空間へ同じ時刻で重ねられた結果を確認できる |
| `su17` | 利用者 | 見失い区間と再拘束の不確実性を、理由付きで把握できる |
| `su18` | 利用者 | 同じ時刻の位置関係をハイライトし、<br>`attention point` から注視区間、滞留箇所、往復や交錯の兆候を絞り込める |
| `su19` | 利用者 | 生成済みの閲覧成果物を操作し、`3DGS` 空間表現、経路、<br>同時刻ハイライトを同じ review 文脈で扱える |
| `sd1` | 運営者 | 4 分担の境界と出力契約だけで、開発と運用を継続できる |
| `sd2` | 運営者 | 抽出 bundle を見れば raw と<br>`trajectreview` 派生出力の境界を追える |
| `sd3` | 運営者 | 抽出直後の bundle だけで `SpaceReconstruction` 着手可否と<br>blocker を判断できる |
| `sd4` | 運営者 | 入力補正、モデル生成、レビュー操作を、app 単位で分けて実行できる |
| `sd5` | 運営者 | 統合 app からも同じ workflow を通しで扱え、<br>手戻り時にどの app 範囲で問題が起きたかを即座に切り分けられる |
| `sd6` | 運営者 | 4 app の各画面で mock ではなく直近の実 bundle を読み、<br>同じ project truth で UX 確認できる |
| `sd7` | 運営者 | `trajectreview-modeling` から request 起点の local sample と<br>handoff request を生成し、PC 上で logic を先に検証できる |
| `sd8` | 運営者 | 指定した `Google Drive` directory を `Colab` 側が読み、<br>実行状態と result URL を返す contract を維持できる |
| `sd9` | 運営者 | `trajectreview-modeling` だけで `DA3Metric-Large` の metric depth 推定、<br>`ARCore pose` / intrinsics 統合、`GNSS` なしでも成立する `3DGS` 系主空間モデル生成の成否を確認でき、<br>必要になった時は複数 route 比較へ広げられる |
| `sd10` | 運営者 | 比較結果から暫定採用 route を決め、<br>以後の既定 route と research route を分けて運用できる |
| `sd11` | 運営者 | `UX-only` 確認、契約固定、local sample、本機能完成を別 gate として追跡できる |

### System Behaviors

| behavior-id | 区分 | 内容 |
| --- | --- | --- |
| `bu1` | 利用者起点 | `InputPackaging` app は入力セッション folder またはその 1 段上の parent directory を選択し、<br>`session_manifest.json` / `manifest.json`、`video_frame_timestamps.csv` / `frames.csv`、`imu.csv`、<br>`bt.jsonl` / `ble_scan.jsonl` / `bt_events.csv` / `bt.csv`、`poses.jsonl` / `arcore_pose.jsonl` / `arcore_pose.csv` を読める |
| `bu2` | 利用者起点 | extractor は raw file を `isensorium/`、<br>派生 file を `trajectreview/` に分離して app export dir へ出力する |
| `bu3` | 利用者起点 | extractor は `sensor_quality.json` に時刻整列 delta、<br>completeness score、pose coverage ratio を含める |
| `bu4` | 利用者起点 | Android UI は抽出元、抽出先、`ready_for_diagnose`、<br>欠落入力、主要 quality 数値を 1 画面で返す |
| `bu5` | 利用者起点 | `trajectreview-correcting` は現場記録開始、停止、session 保存、<br>input export を app 内で完結し、後段が読む concrete bundle を生成する |
| `bu6` | 利用者起点 | `trajectreview-correcting` は最新 session を再読込し、<br>`data-check` により readiness、quality、blocker、recommended correction を返す |
| `bu7` | 利用者起点 | `trajectreview-correcting` は保存済み session 一覧を表示し、<br>取得日時と長さを確認でき、既存 session を選択して再転送、rename、削除できる |
| `bu8` | 利用者起点 | `trajectreview-correcting` は `data-check` 済みの session を選び、<br>送信する data group を選んだうえで、`Storage Access Framework` を通じて選択された `Google Drive` 保存場所へ zip 転送する |
| `bu9` | 利用者起点 | `trajectreview-correcting` は `Storage Access Framework` で選ばれた `Google Drive` 保存場所に対して、<br>選択 session 数に応じた zip を作成して同期できる |
| `bu10` | 利用者起点 | `trajectreview-correcting` は `ARCore Session.update()` で得た同一 frame から pose、frame timestamp、capture timestamp、<br>image intrinsics、texture intrinsics、lens distortion、tracking state を 1 record として保存し、<br>`camera_calibration_summary.json`、`frame_pose_index.csv`、`images/` を派生出力する |
| `bu10a` | 利用者起点 | `trajectreview-correcting` を前面表示している間は端末を自動 sleep させず、`通常計測` では少なくとも `10min` の連続収録を app 側で維持する |
| `bu11` | 利用者起点 | 受理時に、主カメラ動画、主カメラ `IMU`、人物側 `IMU`、<br>任意 `poses` / `gnss` の充足状況を `SessionPackage` へ要約する |
| `bu12` | 利用者起点 | `Diagnose` は、人物映り込みの十分性、不足入力、品質低下、<br>修正理由を `Thin Status` で返す |
| `bu13` | 利用者起点 | 実行可否 gate は、主カメラ動画、主カメラ `IMU`、人物側 `IMU`、<br>空間再構成前提、経路再構成前提の readiness を満たした時だけ `処理を開始` を返す |
| `bu14` | 利用者起点 | 実行 phase は、`Next Action` を常に `完了を待つ` 1 件に保ち、waiting ring と現在段階を別 line で返す |
| `bu15` | 利用者起点 | `DA3Metric-Large` の入力成立が難しい時は、remote modeling を開始せず `入力条件を見直す` を返す |
| `bu16` | 利用者起点 | `trajectreview-modeling` は、スマホまたは PC からの request を受け、<br>`Google Drive` 上の入力 directory と result directory を指定した `Colab` 実行 request を export する |
| `bu17` | 利用者起点 | `trajectreview-modeling` は、remote 実行中の状態を polling し、<br>waiting ring、現在段階、直近更新時刻を request 元画面へ返す |
| `bu18` | 利用者起点 | `trajectreview-modeling` は、remote 実行完了後に `Colab` 側 download URL と result summary を返し、<br>受理後に `SpacePackage`、`TrajectoryPackage`、`modeling_handoff_manifest.json` を更新する |
| `bu19` | 利用者起点 | `SpacePackage` は、`DA3Metric-Large` の metric depth と `ARCore pose` / intrinsics による world projection から得た<br>`ARCore` 基準の主空間、主カメラ path、空間品質、および review 側が消費できる `gs_model` を返す |
| `bu20` | 利用者起点 | `TrajectoryPackage` は、人物個体 `ID` を固定せず、主カメラ path、人物 path、不確実性、再拘束点を<br>同じ `Timeline` 上で返す |
| `bu21` | 利用者起点 | 人物 path の relink は visual match confidence、time gap、anchor proximity、`BT` 主体維持、<br>`IMU` 連続性で判定し、不成立時は不確実性を上げる |
| `bu22` | 利用者起点 | `Verify` は空間品質と経路品質を同時に返し、`Interpret` は同時刻ハイライト候補、`attention point`、<br>滞留箇所、往復や交錯の兆候を返す |
| `bu23` | 利用者起点 | `trajectreview-reviewing` は `ReviewArtifact` 実体を読み、viewer 操作、same-time highlight、<br>`attention point` jump、滞留や交錯の確認操作を返す |
| `bu24` | 利用者起点 | `Assembly` は `3DGS` 系空間表現の操作情報、経路、同時刻ハイライト情報、<br>`attention point` を束ねた `ReviewArtifact` を唯一生成する |
| `bd1` | 運営者起点 | parser は `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を受理する |
| `bd2` | 運営者起点 | `trajectreview` の docs、build、test、生成物経路は `prj-kisaragi_0002` 配下で完結し、要約と生の生成物を分離する |
| `bd3` | 運営者起点 | `InputPackaging` は取得元 raw に加えて、`input_readiness.json`、`sensor_quality.json`、<br>`frame_pose_index.csv`、`member_identity_map.json` を分担インターフェースとして出力する |
| `bd4` | 運営者起点 | 4 分担の各段階は、前段の出力契約だけを読めば次段へ着手できる |
| `bd5` | 運営者起点 | extractor は `video.mp4` と `video_events.jsonl` を含む raw bundle を維持し、後段が主カメラ動画を再利用できる |
| `bd6` | 運営者起点 | extractor は `session_package.json` に source file、timebase、stream count、quality 指標、<br>required / optional input を正規化して出力する |
| `bd7` | 運営者起点 | extractor は `space_handoff_manifest.json` に `ready_for_space_reconstruction`、blocker、<br>利用 artifact、次 action を出力する |
| `bd8` | 運営者起点 | Android UI は `ready_for_space_reconstruction` と blocker を抽出結果画面で返す |
| `bd9` | 運営者起点 | Android project は `trajectreview-correcting`、`trajectreview-modeling`、`trajectreview-reviewing`、<br>統合 app の 4 app module を持ち、共通 source を再利用する |
| `bd10` | 運営者起点 | `trajectreview-correcting` は現場記録、intake / diagnose / correction に必要な画面と文言だけを主表示にする |
| `bd11` | 運営者起点 | `trajectreview-modeling` は `SpaceReconstruction` と `TrajectoryReconstruction` に必要な request 起点、<br>進行表示、result 受け渡しを主表示にする |
| `bd12` | 運営者起点 | `trajectreview-reviewing` は verify / review / same-time highlight を主表示にし、統合 app は全 workflow を束ねる |
| `bd13` | 運営者起点 | correcting、modeling、reviewing、統合 app は、選択した実 bundle から `ReviewContractSnapshot` を再構成し、<br>mock 固定状態に依存しない |
| `bd14` | 運営者起点 | `trajectreview-modeling` は `session_package.json`、`sensor_quality.json`、`space_handoff_manifest.json`、<br>`camera_calibration_summary.json` を読み、`local_model_summary.json`、`colab_job_request.json`、`job_status.json`、<br>`review_artifact_stub.json` を生成する。これは `Colab` 実行前の request preflight と handoff 準備を担う |
| `bd15` | 運営者起点 | `trajectreview-reviewing` と統合 app は `local_model_summary.json` と `review_artifact_stub.json` を読んで、<br>verify / review 状態を組み立てる |
| `bd16` | 運営者起点 | `trajectreview-modeling` は、指定した `Google Drive` directory から zip または `session_root/` を正規化して読み、<br>`Colab` runtime、status 更新、result URL 公開先を再現可能に構築できる |
| `bd16a` | 運営者起点 | `DA3 Colab` runbook は、Drive 上の session zip または session folder 候補を script だけで列挙し、<br>選んだ 1 件を `selected input` として固定したうえで、後続の bootstrap / `TraceCore` one-block が同じ入力から進められる |
| `bd17` | 運営者起点 | `trajectreview-modeling` は `session_package.json`、`arcore_pose.jsonl`、`frame_pose_index.csv`、<br>`camera_calibration_summary.json`、frame 群から、`DA3Metric-Large` 用の前処理入力、metric depth 推定、<br>world projection、`3DGS` 系主空間モデル生成を route 単位で実行できる |
| `bd18` | 運営者起点 | `trajectreview-modeling` は、まず `10s` 前後の整った実動画から `TraceCore` の `multi-frame` densify を行い、<br>`GNSS` なしでも `ARCore` 基準で主空間、主カメラ path、人軌跡の重なりを安っぽく見えない形で返せる。<br>最低限、全体俯瞰、時系列、camera と人の相対表示、滞留や交錯の兆候を検討できることを要件にし、<br>route 比較が必要になった時は、sampling route、intrinsics route ごとの quality、runtime、resource usage、<br>failure reason を `benchmark_summary.json` へ集約できる |
| `bd18a` | 運営者起点 | `trajectreview-modeling` は、`DA3 Giant` または `Giant Large` の Gaussian branch を `infer_gs=True` で別 route として実装できる。`gs_ply` / `gs_video` を生成し、外部 viewer で可視化しつつ、失敗時は rollback baseline である `MetricLarge route`、既存 runbook、既存 artifact 契約を巻き戻しなしで継続できる |
| `bd19` | 運営者起点 | `trajectreview-modeling` は比較結果から `selected_route.json` を生成し、採用 route と research route を分離できる |
| `bd20` | 運営者起点 | `MRL` / `mRL` の `i-pass` は admin `UX check 完了` と本来機能の実行証跡を要件とし、<br>`UX-only`、contract、sample、build / install は補助 gate として別記する |



### 受け入れ基準
| story-id | behavior-id | 観点 | 受け入れ基準 |
| --- | --- | --- | --- |
| `su1` | `bu1`,`bu2`,<br>`bu4` | app 抽出 | `trajectreview` から入力セッション folder を選択し、抽出 bundle を生成できる |
| `su2` | `bu3`,`bu4`,<br>`bd3` | quality 数値 | 時刻整列 delta、completeness score、pose coverage ratio、欠落入力が抽出直後に確認できる |
| `su3` | `bu5` | correcting 本機能 | `trajectreview-correcting` だけで現場記録開始、停止、session 保存、input export まで進められる |
| `su4` | `bu6` | correcting data-check | `trajectreview-correcting` が同じ app 内で `data-check` 結果、blocker、recommended correction を返す |
| `su5` | `bu7`,`bu8`,<br>`bu9` | Google Drive transfer | `trajectreview-correcting` が `data-check` 済み session を 1 件以上選び、`送信Dataset` popup と data 一覧 popup を使って転送対象を確定し、懸念がある data を `▲` 表示したうえで、選択した `Google Drive` 保存場所へ zip を保存できる |
| `su6` | `bu10` | `DA3` 前段 calibration | `trajectreview-correcting` が `ARCore` frame ごとの camera intrinsics、texture intrinsics、lens distortion、frame timestamp を保存し、後段 `DA3 MetricLarge` へ渡せる |
| `su6a` | `bu10a` | 長時間収録安定性 | `trajectreview-correcting` を前面表示したまま `通常計測` で `10min` 収録しても、screen off や lifecycle stop を原因に記録が途切れない |
| `su7` | `bu11`,`bd1`,<br>`bd3` | 受理契約 | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意 `poses` / `gnss`、追加出力の有無が 1 つの要約として読め、`GNSS` なしでも `ARCore` 基準で処理前提を判断できる |
| `su8` | `bu12` | diagnose UX | 人物映り込みの十分性、不足入力、品質低下、修正理由が `Thin Status` で読める |
| `su9` | `bu13` | 実行可否 gate | readiness 未達時は `処理を開始` を返さず、修正 action を返す |
| `su10` | `bu14` | 実行 UX | `Next Action` は常に 1 件で、waiting ring と現在段階は補足 line に分離される |
| `su11` | `bu15` | パイプライン安全性 | 主空間再構成 failure 時に remote modeling を開始せず、入力見直し理由を返す |
| `su12` | `bu16` | modeling request 起点 | `trajectreview-modeling` がスマホまたは PC 起点で入力 directory と result directory を指定した remote 実行 request を作成できる |
| `su13` | `bu14`,`bu17` | waiting UX | waiting ring が回り続け、現在段階と直近更新時刻が request 元画面で読める |
| `su14` | `bu18` | result download 導線 | 処理完了時に download URL と result summary が表示され、次段へ進める |
| `su15` | `bu19` | `TraceCore` 確認 | 主空間、主カメラ path、人軌跡を重ねて見られ、全体俯瞰、時系列、相対表示に加え、滞留や交錯の兆候を検討できる |
| `su16` | `bu20`,`bu21` | 人物経路確認 | 人物個体 `ID` が未確定でも、人物 path が主空間へ重ねられ、不確実区間と再拘束点が識別できる |
| `su17` | `bu21` | 不確実性 | 再拘束失敗時に不確実性 mode と理由が更新される |
| `su18` | `bu22` | ハイライト | 同じ時刻の位置関係と `attention point` に時間範囲と理由が入り、滞留箇所、往復、交錯の兆候を絞り込める |
| `su19` | `bu23`,`bu24` | 閲覧成果物 | `ReviewArtifact` を開き、`3DGS` 操作、経路表示、同時刻ハイライト、`attention point` を同じ review 文脈で操作できる |
| `sd1` | `bd2`,`bd3`,<br>`bd4` | 独立運用 | docs / build / test が project 内で完結し、段階間契約だけで分担着手できる |
| `sd2` | `bu2`,`bd2` | bundle 境界 | `isensorium/` と `trajectreview/` が分離され、raw と派生出力を誤読しない |
| `sd3` | `bd5`,`bd6`,<br>`bd7`,`bd8` | 後段 handoff | `video.mp4` を含む raw bundle と `session_package.json` / `space_handoff_manifest.json` だけで `SpaceReconstruction` 着手可否と blocker を判断できる |
| `sd4` | `bd9`,`bd10`,<br>`bd11`,`bd12` | 作業分割 | 補正、モデル生成、レビュー操作を app 単位で分け、各 app が担当段階を明示できる |
| `sd5` | `bd9`,`bd12` | 統合運用 | 統合 app からも同じ workflow を通しで扱え、問題発生時に app 単位で切り分けられる |
| `sd6` | `bd13`,`bd15` | 実データ UX | 各 app が抽出済みまたは modeling 済み bundle を読み、直近実データに基づく状態を表示できる |
| `sd7` | `bd14`,`bd15` | request preflight | `Colab` account 未取得でも local sample model、request payload、reviewing 用 stub を生成し、PC 上で logic を先に検証できる |
| `sd8` | `bd16` | remote 実行運用 | `Google Drive` directory 指定、`Colab` bootstrap、status 更新、result URL 公開先の contract を維持できる |
| `su12`,`sd8` | `bd16a` | Drive input 選択 | `Colab` 上で Drive 内の session zip または session folder 候補を列挙し、選んだ input を後続 bootstrap と `TraceCore` one-block が共通に参照できる |
| `sd9` | `bd17`,`bd18` | `DA3` modeling 確認 | まず `10s` 前後の整った実動画から `TraceCore` の `multi-frame` densify を行い、`GNSS` なしでも主空間、主カメラ path、人軌跡の重なりを用いて全体俯瞰、時系列、相対表示、滞留や交錯の兆候を検討できる。必要になった時は route 比較へ広げられる |
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
| `tu14a` | `bu10a` | correcting keep-awake control | `correcting` 前面表示中は app が `screen off timeout` に入らず、preview と録画 UI を維持できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `tu14b` | `bu10a` | correcting long-run recording stability | `通常計測` で `10min` 連続収録しても screen off を契機とした lifecycle stop や記録中断が発生しない | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/RecordingCoordinator.kt` |
| `tu15` | `bu11` | `SessionPackage` intake summary | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意入力、時刻基準、品質状態を 1 summary に落とせる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `tu16` | `bu12` | `Thin Status` diagnose formatter | 人物映り込みの十分性、不足入力、品質、理由を `phase`、`pipeline`、`data_health`、`quality`、`issues` で返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu17` | `bu13` | execute readiness gate | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、空間再構成前提、経路前提がそろわない限り `処理を開始` を返さない | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu18` | `bu14` | run phase waiting UX | run phase の `Next Action` が常に 1 件で、waiting ring と現在段階を別 line に出せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu19` | `bu15` | remote modeling safety gate | 入力成立が難しいとき remote modeling を開始しない | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu20` | `bu16` | remote modeling request manifest | `modeling` app が request 元、入力 directory、result directory、job parameter、status 取得先を machine-readable に出力できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `tu21` | `bu17` | waiting ring status sync | request 元画面が polling により waiting ring、現在段階、直近更新時刻を同期表示できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `tu22` | `bu18` | completion download URL import | remote modeling 完了後に download URL と result summary を返し、`SpacePackage`、`TrajectoryPackage`、`modeling_handoff_manifest.json` を更新できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `tu23` | `bu19` | `SpacePackage` coordinate contract | 主カメラ path と主空間基準を返し、`GNSS` がない時に主 `ARCore` local 空間を唯一基準として返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu24` | `bu20` | `TrajectoryPackage` timeline registration | 人物個体 `ID` を固定せず、主カメラ path、人物 path、不確実性、再拘束点を同じ時刻軸で返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu25` | `bu21` | relink uncertainty classifier | visual match confidence、time gap、anchor proximity、`BT` 維持情報で不確実性を決める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu26` | `bu22` | verify quality summary | `space` と `trajectory` の quality、同時刻比較の弱点、weak area に加え、滞留箇所、往復、交錯の兆候を同時に返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu27` | `bu22` | interpret attention point synthesis | `attention point` と同時刻ハイライトに時間範囲、理由、不確実区間情報を持たせ、注視区間を絞り込める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `tu28` | `bu23` | review artifact viewer | `reviewing` app が実 `ReviewArtifact` を読み、viewer と timeline 操作、same-time highlight、`attention point` jump、滞留や交錯の確認操作を提供できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/reviewing/` |
| `tu29` | `bu24` | `ReviewArtifact` boundary contract | `Assembly` だけが `3DGS` 操作、経路表示、同時刻ハイライト、`attention point` を含む `ReviewArtifact` を生成する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
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
| `td22` | `bd15` | reviewing actual bundle state | `reviewing` app と統合 app が modeling 結果を読み、verify / review 状態、同時刻ハイライト候補、`attention point` 候補へ反映できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `td14` | `bd16` | drive directory bootstrap intake | `Colab bootstrap package` が指定した `Google Drive` directory から zip または `session_root/` を正規化して読める | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td14a` | `bd16a` | Drive input candidate scan and select | runbook が Drive 上の session zip / session folder 候補を列挙し、selected input を固定して、後続 `Step 1` と `MRL-7` one-block が hardcoded path なしで同じ入力を読める | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md` |
| `td15` | `bd16` | remote status and result locator | `job_status.json` に stage、updated_at、result availability、download URL を正規化できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td16` | `bd17` | `DA3Metric-Large` input manifest | `modeling` app が frame sampling、intrinsics mode、projection option を route 単位で `experiment_manifest.json` と `da3_input_manifest.json` に出力できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `td17` | `bd17` | metric depth and space runner | `DA3Metric-Large` の少なくとも 1 route を `Colab` で実行し、depth、world projection、`3DGS` 系主空間モデル生成に必要な出力を保存できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td18` | `bd17` | space reconstruction report | `metric scale confidence`、`depth continuity`、`point count estimate`、`gs_model` 生成結果、failure reason を `depth_estimation_report.json` と `space_quality.json` に正規化できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td19` | `bd18` | `TraceCore` multi-frame visible reconstruction | `10s` 前後の整った実動画から複数 frame を sampling し、world point cloud を統合して、`GNSS` なしでも主空間、主カメラ path、人軌跡を重ねた最小表示を返し、全体俯瞰、時系列、相対表示、滞留や交錯の兆候を検討できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td19a` | `bd18a` | `DA3 Giant` Gaussian branch `gs_ply` 実装 | `fps = 1`、`frames = 60`、`process_res = 504`、`chunk = 20` または `30` の入力条件で `infer_gs=True` を有効化し、`gs_ply` / `gs_video` の少なくとも片方を `Colab` に保存できる。失敗時も rollback baseline である `MetricLarge route` の runbook と artifact 契約を壊さない | p-done | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td19b` | `bd18a` | `gs_ply` external viewer 実装 | `gs_ply` を `SuperSplat`、`PlayCanvas Model Viewer`、または同等 viewer のいずれか 1 つで開ける。admin が `自由視点 scene として読める` と判断でき、同時に top camera 専用 renderer を別段で作る判断材料になる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td20` | `bd18` | intrinsics route benchmark aggregation | 少なくとも 2 つの intrinsics / projection route の結果について、quality、runtime、resource usage、failure reason を同一比較表へ集約できる | ready | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `td21` | `bd19` | selected route decision artifact | 暫定採用 route、不採用理由、research route、再評価条件を `selected_route.json` に保存できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `td23` | `bd20` | gate classification rule trace | `UX-only`、contract、sample、本機能の区別が `ux-b2t-hypo.md`、`admin-mrl-test-method.md`、`admin-mrl-test-evidence.md` で矛盾なく追える | ready | `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/` |

### 実行方針
| 対象 `MRL` | phase | 主に扱う `task_id` | 狙い | 現在の進め方 |
| --- | --- | --- | --- | --- |
| `MRL-1` | `correcting` | `tu1`-`tu7`, `tu12`-`tu14` | 記録、抽出、`data-check`、calibration 診断を 1 app UX として固める | `correcting` の記録系と品質診断系を先に閉じ、後段へ渡せる bundle を安定化する |
| `MRL-2` | `correcting` | `tu8`-`tu11`, `td6`-`td8` | `Google Drive` 転送、raw video 維持、handoff bundle 生成を固める | 転送導線と handoff 契約を同じ batch で追い、`SpaceReconstruction` 着手可否まで閉じる |
| `MRL-2S` | `correcting` | `tu14a`-`tu14b` | screen off を回避し、`通常計測` の長時間連続収録を固める | 現場収録が `1min` 超で止まる問題を切り離して閉じ、後段の input 信頼性を上げる |
| `MRL-3` | `modeling` | `td13`, `tu20` | bootstrap / install と request 起点の導線を固める | runbook と request preflight を先にそろえ、remote 実行前の入口を固定する |
| `MRL-4` | `modeling` | `td12`, `td22`, `td14`, `tu18`, `tu21`, `td23` | 実 bundle 読込、request preflight、directory intake、review 側の状態読込を固める | 実データ snapshot と remote intake を先に通し、review 側は stub と結果読込で追従させる |
| `MRL-5` | `modeling` | `td16`-`td18`, `tu22`, `tu23` | single-frame `3DGS` smoke と `SpacePackage` 契約を固める | `DA3Metric-Large` の最小 route を通し、主空間要約と download 導線を残す |
| `MRL-6` | `modeling` | `tu22`, `tu23`, `td23` | evidence bundle の取得、download、local 再参照導線を固定する | notebook evidence と local artifact を product 側 evidence として残せる状態を維持する |
| `MRL-7` | `modeling` | `td19` | `TraceCore` の `multi-frame` densify と高価値な見方を検討できる最小表示を固める | `10s` 前後の整った実動画で、全体俯瞰、時系列、相対表示、滞留、交錯を読めるかを first target に置く |
| `MRL-8` | `modeling` | `td14a` | runbook 本体の前段で Drive 上の任意 input を script だけで選び、後続 bootstrap と `TraceCore` one-block へ同じ入力を渡せるようにする | hardcoded zip 編集を廃止し、fresh runtime で入力差し替えの再現性を上げる |
| `MRL-9` | `modeling` | `td19a`, `td19b` | `DA3 Giant` / `Giant Large` の Gaussian branch を `infer_gs=True` で実装し、`gs_ply` / `gs_video` 生成と外部 viewer 可視化を first route として固める | rollback baseline の `MetricLarge route` を維持したまま `Colab-first` 実装 route として進め、成立後に後続 top camera renderer へ接続する |
| `MRL-**` | `reviewing` / `system統合` | `tu24`-`tu29`, `td20`-`td23` | route 比較、採用 route 固定、reviewing viewer、統合 UX を順次切り出す | admin が手を動かす実態に合わせ、比較、viewer、handoff、統合を後続 gate へ分割する |

### 現在の見立て
| 区分 | 対象 `task_id` | 現在の見立て | 対応する `MRL` | 補足 |
| --- | --- | --- | --- | --- |
| `correcting` 基礎 | `tu1`-`tu7`, `td1`-`td8` | 契約実装、project 境界 scan、output routing 実行まで通っており、この範囲は `p-done` と読める | `MRL-1`, `MRL-2` | Python unittest、Android unit test、PowerShell script 実行で入口契約から成果物 routing まで固定した |
| 転送導線 | `tu8`-`tu11` | 転送 close 導線は `現場撮影データ保存 -> data-check -> Google Drive転送 -> handoff bundle` で閉じる前提にそろっている | `MRL-2` | 事前設定は `転送先を選択 -> URL を確認または変更 -> 保存先fileを設定する -> Google Drive 上で保存先 file を選ぶ` を既定導線とする |
| `modeling` 入口 | `td13`, `tu20`, `td12`, `td14`, `tu18`, `tu21`, `td23`, `td22` | bootstrap / install、実 bundle 読込、request preflight、directory intake、review 側の状態読込までそろった範囲は `p-done` と読める | `MRL-3`, `MRL-4` | `td9` 以降の `modeling` / `reviewing` task は基礎として有効だが、本機能 close には未達である |
| single-frame 主空間 | `td16`-`td18`, `tu22`, `tu23` | `correcting` 実データを使った single-frame `3DGS` 系主空間モデル候補の smoke 生成と artifact 取得までを根拠に `p-done` と読める | `MRL-5` | `SpacePackage` と download 導線の最小契約は通っている |
| evidence 再参照 | `tu22`, `tu23`, `td23` | notebook evidence と local downloaded artifact bundle を product 側 evidence として取得できる段まで通っている | `MRL-6` | product 側 evidence として再参照できることを主に見る |
| `TraceCore` 次段 | `td19` | 次段の first target は、実 session の最長連続 windowを使って gaussian parameter を正式 artifact として扱える形へ寄せ、`TraceCore` の最小表示へ進むことである | `MRL-7` | `MRL-7` はこの段で `p-done`。次は後続 `MRL-**` として viewer 向け形式、長時間 optimization、multi-view 拡張へ進む |
| `Drive input 選択` | `td14a` | runbook の前段で任意 input を選べる script を追加し、selected input を本体と `MRL-7` one-block へ受け渡す段は成立済みである | `MRL-8` | hardcoded path を除去し、admin が Colab 上で入力差し替えを手編集なしで進められる状態まで `p-done` |
| `Giant Gaussian branch` | `td19a`,`td19b` | `DA3 Giant` / `Giant Large` と `infer_gs=True` を `Colab-first` 実装 route として進め、`gs_ply` / `gs_video` 生成と外部 viewer 可視化を先に固める | `MRL-9` | rollback baseline は `MetricLarge route` とし、`MRL-9` artifact は別 output root へ保存する |
| 後続 backlog | `tu24`-`tu29`, `td20`-`td23` | `multi-route` 比較、`selected_route.json` 固定、request / status UX、result 返却、viewer 実装、統合 UX は後続 `MRL-**` へ残っている | `MRL-**` | task 実測で課題の大小が見えた時点で `MRL` / `mRL` の切り方を調整する |
| 共通方針 | `TDD` 全体 | `MRL` の達成品質として求める UX は薄めず、north star に沿って各段の到達像を明記し続ける | 全体 | modeling は admin の手作業を含むため、後続 `MRL` の粒度は実測に合わせて更新する |

## `Main Release Line` 対応表
- `admin UX確認手順` は [admin-mrl-test-method.md](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-method.md) の章名または操作手順番号をそのまま書く。
- `admin evidence` は [admin-mrl-test-evidence.md](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md) の章名をそのまま書く。

### 利用者主導 MRL
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
| `MRL-2S` | `-` | `correcting` 前面表示中の screen off 回避と、`通常計測` の `10min` 連続収録安定性を固める | `su6a` | `bu10a` | `tu14a`,`tu14b` | `active` | `active` | 操作手順 16-19 と長時間収録追補 | 2026-03-31 `MRL-2S` bounded stop candidate evidence |
| `MRL-2S` | `mRL-2S.1` | app 前面表示中の keep-awake により、自動減光や screen off で収録が止まらないことを確認する | `su6a` | `bu10a` | `tu14a` | `active` | `active` | 操作手順 16-19 | 2026-03-31 `MRL-2S` bounded stop candidate evidence |
| `MRL-2S` | `mRL-2S.2` | `通常計測` で `10min` 連続収録しても app が落ちず、session が finalizable であることを確認する | `su6a` | `bu10a` | `tu14b` | `active` | `active` | 操作手順 16-19 と長時間収録追補 | 2026-03-31 `MRL-2S` bounded stop candidate evidence |
| `MRL-3` | `-` | `Colab` 実行前の<br>package / config / runbook 導線と<br>bootstrap / install を<br>たどれることを確認する | `sd7`,`su12` | `bd14`,`bu16` | `td13`,`tu20` | `p-done` | `p-done` | modeling batch<br>操作手順 4-6<br>da3_colab_<br>clean_bootstrap_<br>runbook.md | modeling batch 定義,<br>2026-03-29 modeling bootstrap candidate evidence |
| `MRL-3` | `mRL-3.1` | `Colab` 実行前の package / config / runbook 導線を手動でたどれることを確認する | `sd7`,`su12` | `bd14`,`bu16` | `td13`,`tu20` | `p-done` | `p-done` | modeling batch <br>操作手順 4-6 と<br>da3_colab_<br>clean_bootstrap_<br>runbook.md | 2026-03-29 modeling bootstrap candidate evidence |
| `MRL-4` | `-` | `trajectreview-modeling` で<br>実 bundle 読込、<br>request preflight、<br>review 側 state 組立て、<br>`Google Drive` directory intake までを成立させる | `sd6`,`sd7`,<br>`sd8`,`su12`,<br>`su19`,`sd11` | `bd13`,`bd14`,<br>`bd15`,`bd16`,<br>`bu16`,`bd20` | `td12`,`td13`,<br>`td22`,`td14`,<br>`tu20`,`td23` | `p-done` | `p-done` | modeling batch<br>操作手順 1-9 | modeling batch 定義,<br>2026-03-29 modeling preflight close evidence |
| `MRL-4` | `mRL-4.1` | 実 bundle snapshot 読込、request preflight 生成、review 側 state 組立てを確認する | `sd6`,`sd7`,<br>`su12`,`su19` | `bd13`,`bd14`,<br>`bd15`,`bu16` | `td12`,`td13`,<br>`td22`,`tu20` | `p-done` | `p-done` | modeling batch<br>操作手順 1-6 | 2026-03-26 MRL-4 candidate evidence,<br>2026-03-29 modeling preflight close evidence |
| `MRL-4` | `mRL-4.2` | `Google Drive` directory<br>bootstrap を確認する | `sd8`,`su12` | `bd16`,`bu16` | `td14`,`tu20` | `p-done` | `p-done` | modeling batch<br>操作手順 7-9<br>runbook の<br>事前準備 / 準備確認 | 2026-03-29 modeling bootstrap candidate evidence,<br>2026-03-29 modeling preflight close evidence |
| `MRL-5` | `-` | `DA3Metric-Large` による<br>single-frame `3DGS` 系<br>主空間モデル生成 smoke を<br>成立させる | `su14`,`su15`,<br>`sd9`,`sd11` | `bd17`,`bu18`,<br>`bu19`,`bd20` | `td16`,`td17`,<br>`td18`,`tu22`,<br>`tu23`,`td23` | `p-done` | `p-done` | modeling batch<br>操作手順 13-18<br>p-done / i-pass の判断<br>fail の判断<br>runbook の <br>Candidate Bootstrap v1 | modeling batch 定義,<br>2026-03-29 MRL-5 3DGS smoke candidate evidence |
| `MRL-5` | `mRL-5.1` | `DA3` input manifest と route export を確認する | `sd9` | `bd17` | `td16` | `p-done` | `p-done` | modeling batch <br>操作手順 13-14 | 2026-03-29 MRL-5 3DGS smoke candidate evidence |
| `MRL-5` | `mRL-5.2` | `Colab` 上の metric depth と `3DGS` 系主空間モデル生成を確認する | `sd9`,`su14` | `bd17`,`bu18` | `td17`,`tu22` | `p-done` | `p-done` | modeling batch<br>操作手順 15-17 と<br>da3_colab_<br>clean_bootstrap_<br>runbook.md の<br>Candidate Bootstrap v1 | 2026-03-29 MRL-5 3DGS smoke candidate evidence |
| `MRL-5` | `mRL-5.3` | `depth_estimation_report.json`、`space_quality.json`、`gs_model` を含む主空間要約を確認する | `su15`,`sd9` | `bu19`,`bd17` | `tu23`,`td18` | `p-done` | `p-done` | 未収載 | 2026-03-29 MRL-5 3DGS smoke candidate evidence |
| `MRL-6` | `-` | `modeling` の smoke 生成物を<br>admin が notebook / local download で取得し、<br>product 側 evidence として<br>再参照できることを確認する | `su15`,`sd11` | `bu19`,`bd20` | `tu23`,`td23` | `p-done` | `p-done` | da3_colab_<br>clean_bootstrap_<br>runbook.md<br>の Candidate 拡張状況 | 2026-03-29 modeling evidence bundle close evidence |
| `MRL-6` | `mRL-6.1` | `Google Colab` 実行 notebook を product 側 evidence として保存し、再参照できることを確認する | `sd11` | `bd20` | `td23` | `p-done` | `p-done` | da3_colab_<br>clean_bootstrap_<br>runbook.md の<br>Candidate 拡張状況 | 2026-03-29 modeling evidence bundle close evidence |
| `MRL-6` | `mRL-6.2` | local downloaded smoke artifact 一式を product 側 evidence として保存し、再参照できることを確認する | `su15`,`sd11` | `bu19`,`bd20` | `tu23`,`td23` | `p-done` | `p-done` | da3_colab_<br>clean_bootstrap_<br>runbook.md の<br>Candidate 拡張状況 | 2026-03-29 modeling evidence bundle close evidence |
| `MRL-7` | `-` | `10s` 前後の整った実動画から<br>`TraceCore` として `multi-frame` で、<br>利用者が主空間、主カメラ経路、<br>人軌跡の関係を見比べ、<br>全体俯瞰、時系列、相対表示、<br>滞留や交錯の兆候を検討できる<br>最小表示を得る | `sd9`,`su15`,<br>`sd11` | `bd18`,`bu19`,<br>`bd20` | `td19`,`td23` | `p-done` | `p-done` | 操作手順 27-33 と<br>gaussian artifact 確認 | 2026-03-30 `mRL-7.2` gaussian short-optimization candidate evidence |
| `MRL-7` | `mRL-7.1` | 実 session の最長連続 window を正として `multi-frame` sampling、depth batch、world fusion、preview closeout を行い、`TraceCore` 最小表示の前段となる multi-frame 点群 candidate-visible-proof を得る | `sd9`,`su15` | `bd18`,`bu19` | `td19` | `p-done` | `p-done` | 操作手順 27-33 | 2026-03-30 `mRL-7.1`<br>multi-frame point-fusion close evidence |
| `MRL-7` | `mRL-7.2` | multi-frame point cloud から gaussian parameter を初期化し、短い optimization を通して正式 gaussian artifact へ寄せる。admin の目視で取得背景に近い構図への改善を確認する | `su15`,`sd11` | `bd18`,`bd20` | `td19`,`td23` | `p-done` | `p-done` | 操作手順 27-33 と<br>gaussian artifact 確認 | 2026-03-30 `mRL-7.2` gaussian short-optimization candidate evidence |
| `MRL-8` | `-` | `Colab` 上で Drive 内の<br>session zip / session folder 候補を列挙し、<br>選んだ input を runbook 本体と<br>`MRL-7` one-block が共通参照できる状態を固める | `su12`,`sd8`,<br>`sd11` | `bd16`,`bd16a`,<br>`bd20` | `td14`,`td14a`,<br>`td23` | `p-done` | `p-done` | runbook の<br>準備確認 2-4 と<br>`Step 8d`-`8e` | 2026-03-31 `MRL-8`<br>Drive input select close evidence |
| `MRL-8` | `mRL-8.1` | Drive input candidate scan により session zip / session folder 候補を index 付きで列挙し、selected input を固定できる | `su12`,`sd8` | `bd16a` | `td14a` | `p-done` | `p-done` | runbook の<br>準備確認 2-3 と<br>`Step 8a4` | 2026-03-31 `MRL-8`<br>Drive input select close evidence |
| `MRL-8` | `mRL-8.2` | selected input を `Step 1` と `MRL-7` one-block の両方が共通に読み、hardcoded path なしで `session_root` 正規化へ進める。現時点の運用は `Run all` ではなく、widget 選択を 1 回挟んでから残りを順次実行する | `su12`,`sd8`,<br>`sd11` | `bd16`,`bd16a`,<br>`bd20` | `td14`,`td14a`,<br>`td23` | `p-done` | `p-done` | runbook の<br>準備確認 4、<br>`Step 8d`、<br>`Step 8e` | 2026-03-31 `MRL-8`<br>Drive input select close evidence |
| `MRL-9` | `-` | `DA3 Giant` または<br>`Giant Large` の<br>Gaussian branch を<br>`infer_gs=True` で実装し、<br>`gs_ply` / `gs_video` 生成と<br>外部 viewer 可視化を first route として固める | `sd9`,`su15`,<br>`sd11` | `bd18a`,`bd20` | `td19a`,`td19b`,<br>`td23` | `active` | `active` | temp-da3Giant_<br>colab_evid_<br>runbook.md | 2026-03-31 `mRL-9.1`<br>giant infer_gs close evidence |
| `MRL-9` | `mRL-9.1` | `fps = 1`、`frames = 60`、`process_res = 504`、`chunk = 20` または `30` を first config とし、`infer_gs=True` で `gs_ply` / `gs_video` の少なくとも片方を `Colab` に保存できる | `sd9`,`sd11` | `bd18a` | `td19a` | `p-done` | `p-done` | temp-da3Giant_<br>colab_evid_<br>runbook.md | 2026-03-31 `mRL-9.1`<br>giant infer_gs close evidence |
| `MRL-9` | `mRL-9.2` | `gs_ply` を `SuperSplat`、`PlayCanvas Model Viewer`、または同等 viewer のいずれかで開き、自由視点 scene として読めることを確認する。top camera renderer と path overlay は後段へ送る | `su15`,`sd11` | `bd18a`,`bd20` | `td19b`,`td23` | `ready` | `ready` | `未収載` | `未収載` |

### 利用者向け後続 `MRL-**` に紐づく運営者補助 MRL
| MRL | mRL | gate test 項目 | story-id | behavior-id | task-id | 現在 gate | UX評価状態 | admin UX確認手順 | admin evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MRL-**` | `-` | 利用者向け後続 `MRL-**` を支える<br>補助 MRL として、route 比較、採用 route 固定、<br>request / status UX、result 返却、reviewing viewer、正式統合を<br>実測に応じて順次切り出す | `sd6`,`sd9`,<br>`sd10`,`su10`,<br>`su12`,`su13`,<br>`su18`,`su19`,<br>`sd11` | `bd16`,`bd18`,<br>`bd19`,`bu14`,<br>`bu16`,`bu17`,<br>`bu18`,`bu22`,<br>`bu23`,`bu24`,<br>`bd20` | `td20`,`td21`,<br>`td15`,`tu18`,<br>`tu20`,`tu21`,<br>`tu22`,`tu26`,<br>`tu27`,`tu28`,<br>`tu29`,`td23` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.1` | `multi-route` 比較を行い、quality、runtime、resource usage、failure reason を同一 session 上で比較できる | `sd9`,`sd11` | `bd18`,`bd20` | `td20`,`td23` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.2` | 暫定採用 route を `selected_route.json` として固定し、research route と再評価条件を追える | `sd9` | `bd19` | `td21` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.3` | request 元から input directory、result directory、route id を束ねて remote 実行 request を作り、waiting ring と `job_status.json` を読み続けられる | `su10`,`su12`,<br>`su13` | `bd16`,`bu14`,<br>`bu16`,`bu17` | `td15`,`tu18`,<br>`tu20`,`tu21` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.4` | remote 完了後に download URL と result summary を返し、`SpacePackage`、`TrajectoryPackage`、`ReviewArtifact` handoff を後段へ渡せる | `sd10`,`su14`,<br>`su19` | `bu18`,`bu23`,<br>`bu24` | `tu22`,`tu28`,<br>`tu29` | `ready` | `ready` | `未収載` | `未収載` |
| `MRL-**` | `mRL-**.5` | reviewing viewer で主空間、主カメラ経路、人物経路、same-time highlight、`attention point`、滞留や交錯の兆候を同じ review 文脈で扱える | `su18`,`su19` | `bu22`,`bu23`,<br>`bu24` | `tu26`,`tu27`,<br>`tu28`,`tu29` | `ready` | `ready` | `未収載` | `未収載` |
