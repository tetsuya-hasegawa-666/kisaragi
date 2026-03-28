# B2T-Plans-Results

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
| `ISS-001` | `InputPackaging` の入口を `correcting` 中心へ寄せた後、統合 app / legacy intake をどこまで同格に扱うか | `InputPackaging` の UX、truth、後段説明 | admin 判断により、開発中から実使用まで全入口を開けたまま併存させ、説明順だけを運用上の既定に留める | `close` | `project-truth.md`, `ux_check_manual.md` |
| `ISS-002` | `Google Drive` 転送先の document grant を持続前提にするか | `MRL-5D` の実運用可否 | admin 判断により grant 持続前提を捨て、`転送先を選択` を毎回必須にする | `close` | `project-truth.md`, `mrl-ux-valid.md` |
| `ISS-003` | `Google Drive` 側は zip、端末側は `<session_id>/` であり、どの段階で unzip を正規化するか | handoff 運用、admin 手順、実装分担 | `modeling` の `Colab bootstrap package` が unzip と配置正規化を担う方針へ決定した | `close` | `project-truth.md`, `ux_check_manual.md` |
| `ISS-005` | `Colab all-in modeling` package と `correcting` の PC install package の配布形式をどこまで共通化するか | `INITL` の粒度、導入 UX | `INITL` を分離導入し、package 構成は `0002` 内で設計を開始する | `small-open` | `project-truth.md`, `b2t-plans-result.md` |
| `ISS-004` | `疑問点不整合一覧` の粒度を `MRL` closeout と同じ粒度まで細かくするか | 文書運用コスト | 現在は admin 判断が要るものと Codex の小疑問だけを集約する | `no judge` | `AGENTS.md`, `b2t-plans-result.md` |
| `ISS-006` | Android 標準保存画面で `Google Drive` provider へ切り替える操作が初見 user に分かりにくい | 多人数展開時の導入 UX | 現時点は手順明記のみ。利用者が増えたら help 導線を追加する | `small-open` | `ux_check_manual.md`, `project-truth.md` |

### 現在の重点

- `T1` から `T16` は contract 実装、test、routing 実行で成立したが、admin `UX check` 未完のため対応 `MRL` / `mRL` は `active` として扱う
- `MRL-5` と `MRL-6` は、入力契約と handoff artifact の整備までは進んだが、`correcting` から `modeling` への end-to-end handoff は未完である
- `MRL-5C` を `trajectreview-correcting` 専用 gate とし、現場記録後に同じ app 内で `data-check` と correction guidance を返せる実装までは進んだが、`pass` は admin `UX check` 待ちである
- `MRL-5D` を `trajectreview-correcting` 専用 gate とし、`1 回以上 data-check` の後に `Google Drive` 保存場所へ zip 転送する実装を追加する
- `MRL-7` と `MRL-8` は、4 app の骨格、build、install、実 bundle 読込、`local sample` による局所 logic 確認まで進んだが、本来機能の完成 gate としては `active` に巻き戻す
- `trajectreview-correcting` の現在 focus は、収録停止後の待ち時間短縮と、`品質確認` / 一覧更新 / 転送 UX の安定化である
- `品質確認` は lightweight 判定を先に返し、`frame画像群` は転送要求時だけ生成する構成へ切り替えた
- 保存済み data 一覧の `▲` は lightweight `品質確認` 再実行で更新し、軽微な項目や `images/` 未生成だけでは付けない運用へ切り替えた
- `Google Drive` 転送は都度 `転送先を選択` 前提へ切り替え、転送 UX は成立したが、多人数向け help は未着手である
- `MRL-5C` の範囲では、`trajectreview-correcting` 単体で source session を保存し、`sensor_quality.json`、`session_package.json`、`space_handoff_manifest.json` を生成し、修正指示を返せる実装がある
- `MRL-5C` の calibration export interface は、一時要件を吸収し、`arcore_pose.jsonl` nested schema、`camera_calibration_summary.json`、`frame_pose_index.csv`、`images/`、path pointer を含む handoff へ更新した
- `MRL-5C` には `mRL-5C.4` を追加し、`intrinsics` 不足が `実取得失敗`、`集計上の見え方`、`calibration export 実装前 data` のどれかを切り分ける診断を追跡する
- `MRL-5C` には `mRL-5C.5` を追加し、`corecamera_shared_camera_trial` route でも `OffscreenArCorePoseSampler` から image / texture intrinsics を実取得し、`captureDiagnostics` を実データで検証する
- `MRL-5D` の範囲では、`trajectreview-correcting` 単体で `サンプリング条件設定 / スマホ内保存先選択 / 転送対象準備 -> 現場撮影データ保存 + data-check -> 品質確認済み data の複数選択 -> Google Drive 転送先選択 + 転送実行` を閉じる
- `trajectreview-modeling` は `Colab all-in` を主 route とし、PC 側は source、config、auto-install package、証跡の正本を保持する
- `trajectreview-modeling` は preflight artifact として `experiment_manifest.json`、`da3_input_manifest.json`、`benchmark_summary.json`、`selected_route.json`、Colab notebook / import helper / bootstrap package を持つ
- Colab notebook の `CONFIG` は `session_root` と `result_root` を最小入力とし、残りの route 情報は session bundle 内の artifact から自動で補完する
- `ISS-003` の unzip / 配置正規化責務は `modeling` の `Colab bootstrap package` が担う
- `INITL-1` は `modeling` の `Colab bootstrap package`、source 配置、config、auto-install package を追跡する
- `INITL-2` は `correcting` の PC install package 準備と artifact 互換性を追跡する
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
- 人物 path の視覚再拘束に使う実データ条件が未確定である
- `ReviewArtifact` の最終 viewer 実装先は Android 固定ではない
- 取得元 app data の配置差分は実機ごとの差を吸収する必要がある
- multi-app 化では共通 source を維持しつつ app role を分ける必要がある
- `Colab` account 情報は未取得であり、remote 実行は後続 task とする
- `UX-only` 確認と本機能完成 gate を plan 上で分離していなかったことに加え、admin `UX check` 完了前に `pass` を付けていたため、closeout が過大になった

### 次の確認

1. `trajectreview-modeling` を `DA3Metric-Large` depth 推定 + `ARCore pose` / intrinsics 統合、multi-route 比較、採用 route 運用化の 3 段で閉じる
2. `trajectreview-reviewing` を `ReviewArtifact` 実 viewer と same-time highlight 操作まで閉じる
3. `INITL-1` として `Colab all-in modeling` package の source、config、auto-install 導線を固める

### 作業所有権

- Codex が `project-truth.md`、`b2t-plans-result.md`、`mrl-record.md` の再開基線整備、`MRL-5` 抽出統合作業、以後の `MRL` 継続作業を担当する

## BDD

### 目的文

この章は `prj-kisaragi_0002` の提供価値、`Purpose Story`、`System Behaviors`、`MRL` / `mRL` の対応を定義する。

### 目指す姿

- `trajectreview` は、1 台のスマホカメラとその `IMU` による連続動画、および `IMU` 付き機器を持つ人がその動画へ頻繁に映り込む状況で、最も効果を発揮する
- 連続動画と `IMU` のデータ、および動画なしの `IMU` 付きスマホを携帯する人のデータを入力するだけで、現場の `3DGS`、撮影主体の経路、映り込む人の経路を同じ `3DGS` 空間上へ表示できる
- 経路は時系列情報を持ち、同じ時刻の位置関係をハイライトできる

### 提供方針

- 最適条件は 1 台の主カメラ動画と、映り込む人の `IMU` データである
- `GNSS` は任意入力とし、なくても主 `ARCore` 空間を基準に成立させる
- `Timeline` を統合キーとして、主カメラ path と人物 path を同時刻で束ねる
- まず受理、診断、実行可否を固め、その後に空間、経路、閲覧を分離実装する
- 閲覧成果物は `3DGS` の操作、経路表示、同時刻ハイライトを一体で扱う

### Purpose Story

- `s1`: 利用者は、主カメラ動画と主カメラ `IMU`、および人物側 `IMU` の入力がそろっているかを受理時点で把握できる
- `s2`: 利用者は、主カメラ動画に人物が十分映り込んでいるか、不足入力や品質低下とあわせて診断で読める
- `s3`: 利用者は、主空間再構成と人物経路再構成に必要な条件を満たした時だけ `処理を開始` を受け取れる
- `s4`: 利用者は、実行中に今どの段階を処理しているかだけを見ればよい
- `s5`: 利用者は、主空間再構成が成立しない時に `3DGS` 生成へ進まず修正へ戻れる
- `s6`: 利用者は、1 台の主カメラ動画から作られた `3DGS` と主カメラ経路を確認できる
- `s7`: 利用者は、人物側 `IMU` と映り込みを使って人物経路が主空間へ重ねられた結果を確認できる
- `s8`: 利用者は、見失い区間と再拘束の不確実性を理由付きで把握できる
- `s9`: 利用者は、`3DGS` 上で主カメラ経路と人物経路を同時刻比較できる
- `s10`: 利用者は、同じ時刻の位置関係をハイライトし、注視すべき区間を絞り込める
- `s11`: 利用者は、生成済み `ReviewArtifact` を viewer で操作し、空間と経路をレビューできる
- `s12`: 運用者は、4 分担の境界と出力契約だけで実装と運用を継続できる
- `s13`: 利用者は、`trajectreview` から入力セッション folder を選択し、抽出結果をその場で得られる
- `s14`: 利用者は、抽出後に時刻整列とデータ確からしさを数値で確認できる
- `s15`: 運用者は、抽出 bundle を見れば raw と `trajectreview` 派生出力の境界を追える
- `s16`: 運用者は、抽出直後の bundle だけで `SpaceReconstruction` 着手可否と blocker を判断できる
- `s17`: 運用者は、入力補正、モデル生成、レビュー操作を app 単位で分けて実行できる
- `s18`: 運用者は、統合 app からも同じ workflow を通しで扱え、手戻り時にどの app 範囲で問題が起きたかを即座に切り分けられる
- `s19`: 運用者は、4 app の各画面で mock ではなく直近の実 bundle を読み、同じ project truth で UX 確認できる
- `s20`: 運用者は、`trajectreview-modeling` から `Colab` 送信前の軽量 local sample model と handoff request を生成し、PC 上で logic を先に検証できる
- `s21`: 利用者は、`trajectreview-correcting` だけで現場記録開始、停止、session 保存、診断前 export まで進められる
- `s21a`: 利用者は、`trajectreview-correcting` の記録停止後に同じ app 内で `data-check` 結果と修正指示を読める
- `s21b`: 利用者は、`trajectreview-correcting` の `data-check` を 1 回以上通した後、`Google Drive` 保存場所へ session zip を転送できる
- `s21c`: 利用者は、`trajectreview-correcting` の記録中に `DA3 MetricLarge` 後段で使う camera intrinsics、texture intrinsics、lens distortion、frame timestamp を同じ `ARCore` frame 単位で残せる
- `s22`: 利用者は、`trajectreview-modeling` だけで `Colab` 実行 request の作成、upload 対象確認、remote result 受理まで進められる
- `s22a`: 運用者は、`trajectreview-modeling` だけで `DA3Metric-Large` の metric depth 推定と `ARCore pose` / intrinsics 統合の成否を確認できる
- `s22b`: 運用者は、同じ session に対して複数の sampling / intrinsics route を同一指標で比較できる
- `s22c`: 運用者は、比較結果から暫定採用 route を決め、以後の既定 route と research route を分けて運用できる
- `s23`: 利用者は、`trajectreview-reviewing` だけで実 `ReviewArtifact` を開き、経路、同時刻ハイライト、`attention point` を操作できる
- `s24`: 運用者は、`UX-only` 確認、契約固定、local sample、本機能完成を別 gate として追跡できる

### System Behaviors

- `b1`: 受理時に、主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意 `poses` / `gnss` の充足状況を `SessionPackage` へ要約する
- `b2`: `Diagnose` は、人物映り込みの十分性、不足入力、品質低下、修正理由を `Thin Status` で返す
- `b3`: 実行可否 gate は、主カメラ動画、主カメラ `IMU`、人物側 `IMU`、空間再構成前提、経路再構成前提の readiness を満たした時だけ `処理を開始` を返す
- `b4`: 実行 phase は、`Next Action` を常に `完了を待つ` 1 件に保ち、現在段階を別 line で返す
- `b5`: `COLMAP.status != READY_FOR_DENSIFICATION` のとき、`3DGS` を開始せず `入力条件を見直す` を返す
- `b6`: `SpacePackage` は、1 台の主カメラ動画から得た主空間基準、主カメラ path、空間品質を返す
- `b7`: `TrajectoryPackage` は、主カメラ path、人物 path、不確実性、再拘束点を同じ `Timeline` 上で返す
- `b8`: 人物 path の relink は visual match confidence、time gap、anchor proximity、`BT` 主体維持で判定し、不成立時は不確実性を上げる
- `b9`: `Verify` は空間品質と経路品質を同時に返し、`Interpret` は同時刻ハイライト候補と `attention point` を返す
- `b10`: `Assembly` は `3DGS` 操作用情報、経路、同時刻ハイライト情報を束ねた `ReviewArtifact` を唯一生成する
- `b11`: parser は `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を受理する
- `b12`: `trajectreview` の docs、build、test、生成物経路は `prj-kisaragi_0002` 配下で完結し、要約と生の生成物を分離する
- `b13`: `InputPackaging` は取得元 raw に加えて、`input_readiness.json`、`sensor_quality.json`、`frame_pose_index.csv`、`member_identity_map.json` を分担インターフェースとして出力する
- `b14`: 4 分担の各段階は、前段の出力契約だけを読めば次段へ着手できる
- `b15`: `InputPackaging` app は入力セッション folder またはその 1 段上の parent directory を選択し、`session_manifest.json` / `manifest.json`、`video_frame_timestamps.csv` / `frames.csv`、`imu.csv`、`bt.jsonl` / `ble_scan.jsonl` / `bt_events.csv` / `bt.csv`、`poses.jsonl` / `arcore_pose.jsonl` / `arcore_pose.csv` を読める
- `b16`: extractor は raw file を `isensorium/`、派生 file を `trajectreview/` に分離して app export dir へ出力する
- `b17`: extractor は `sensor_quality.json` に時刻整列 delta、completeness score、pose coverage ratio を含める
- `b18`: Android UI は抽出元、抽出先、`ready_for_diagnose`、欠落入力、主要 quality 数値を 1 画面で返す
- `b19`: extractor は `video.mp4` と `video_events.jsonl` を含む raw bundle を維持し、後段が主カメラ動画を再利用できる
- `b20`: extractor は `session_package.json` に source file、timebase、stream count、quality 指標、required / optional input を正規化して出力する
- `b21`: extractor は `space_handoff_manifest.json` に `ready_for_space_reconstruction`、blocker、利用 artifact、次 action を出力する
- `b22`: Android UI は `ready_for_space_reconstruction` と blocker を抽出結果画面で返す
- `b23`: Android project は `trajectreview-correcting`、`trajectreview-modeling`、`trajectreview-reviewing`、統合 app の 4 app module を持ち、共通 source を再利用する
- `b24`: `trajectreview-correcting` は現場記録、intake / diagnose / correction に必要な画面と文言だけを主表示にする
- `b25`: `trajectreview-modeling` は `SpaceReconstruction` と `TrajectoryReconstruction` に必要な gate、handoff、進行表示を主表示にする
- `b26`: `trajectreview-reviewing` は verify / review / same-time highlight を主表示にし、統合 app は全 workflow を束ねる
- `b27`: correcting、modeling、reviewing、統合 app は、選択した実 bundle から `ReviewContractSnapshot` を再構成し、mock 固定状態に依存しない
- `b28`: `trajectreview-modeling` は `session_package.json`、`sensor_quality.json`、`space_handoff_manifest.json` を読み、`local_model_summary.json`、`colab_job_request.json`、`review_artifact_stub.json` を生成する
- `b29`: `trajectreview-reviewing` と統合 app は `local_model_summary.json` と `review_artifact_stub.json` を読んで verify / review 状態を組み立てる
- `b30`: `trajectreview-correcting` は現場記録開始、停止、session 保存、input export を app 内で完結し、後段が読む concrete bundle を生成する
- `b30a`: `trajectreview-correcting` は最新 session を再読込し、`data-check` により readiness、quality、blocker、recommended correction を返す
- `b30b`: `trajectreview-correcting` は `data-check` 済みの session を選び、送信する data group を選んだうえで、選択された `Google Drive` 保存場所へ zip 転送する
- `b30e`: `trajectreview-correcting` は保存済み session 一覧を表示し、取得日時と長さを確認でき、既存 session を選択して再転送または rename できる
- `b30c`: `trajectreview-correcting` は `Storage Access Framework` で選ばれた `Google Drive` 保存場所に対して、選択 session 数に応じた zip を作成して同期できる
- `b30d`: `trajectreview-correcting` は `ARCore Session.update()` で得た同一 frame から pose、frame timestamp、capture timestamp、image intrinsics、texture intrinsics、lens distortion、tracking state を 1 record として保存し、`camera_calibration_summary.json` と `frame_pose_index.csv`、`images/` を派生出力する
- `b31`: `trajectreview-modeling` は `Colab` 実行 request を export し、remote 実行結果の受理後に `SpacePackage`、`TrajectoryPackage`、`modeling_handoff_manifest.json` を更新する
- `b31a`: `trajectreview-modeling` は `session_package.json`、`frame_pose_index.csv`、`camera_calibration_summary.json` と frame 群から `DA3Metric-Large` 用の前処理入力、metric depth 推定、world projection を route 単位で実行できる
- `b31b`: `trajectreview-modeling` は sampling route、intrinsics route、ごとの quality、runtime、resource usage、failure reason を `benchmark_summary.json` へ集約できる
- `b31c`: `trajectreview-modeling` は比較結果から `selected_route.json` を生成し、採用 route と research route を分離できる
- `b32`: `trajectreview-reviewing` は `ReviewArtifact` 実体を読み、viewer 操作、same-time highlight、`attention point` jump を返す
- `b33`: `MRL` / `mRL` の `pass` は admin `UX check 完了` と本来機能の実行証跡を要件とし、`UX-only`、contract、sample、build / install は補助 gate として別記する



### 受け入れ基準

| s-id | b-id | 観点 | 受け入れ基準 |
| --- | --- | --- | --- |
| `s1` | `b1`,`b11`,`b13` | 受理契約 | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意 `poses` / `gnss`、追加出力の有無が 1 つの要約として読める |
| `s2` | `b2` | diagnose UX | 人物映り込みの十分性、不足入力、品質低下、修正理由が `Thin Status` で読める |
| `s3` | `b3` | 実行可否 gate | readiness 未達時は `処理を開始` を返さず、修正 action を返す |
| `s4` | `b4` | 実行 UX | `Next Action` は常に 1 件で、現在段階は補足 line に分離される |
| `s5` | `b5` | パイプライン安全性 | 主空間再構成 failure 時に `3DGS` を開始しない |
| `s6` | `b6` | 主空間確認 | 主空間基準、主カメラ path、空間品質が読める |
| `s7` | `b7`,`b8` | 人物経路確認 | 人物 path が主空間へ重ねられ、不確実区間と再拘束点が識別できる |
| `s8` | `b8` | 不確実性 | 再拘束失敗時に不確実性 mode と理由が更新される |
| `s9` | `b7`,`b9` | 同時刻比較 | 主カメラ経路と人物経路が同じ時刻軸で比較できる |
| `s10` | `b9` | ハイライト | 同じ時刻の位置関係と `attention point` に時間範囲と理由が入る |
| `s11` | `b10` | 閲覧成果物 | `ReviewArtifact` に `3DGS` 操作、経路表示、同時刻ハイライトが含まれる |
| `s12` | `b12`,`b13`,`b14` | 独立運用 | docs / build / test が project 内で完結し、段階間契約だけで分担着手できる |
| `s13` | `b15`,`b16`,`b18` | app 抽出 | `trajectreview` から入力セッション folder を選択し、抽出 bundle を生成できる |
| `s14` | `b13`,`b17`,`b18` | quality 数値 | 時刻整列 delta、completeness score、pose coverage ratio、欠落入力が抽出直後に確認できる |
| `s15` | `b16` | bundle 境界 | `isensorium/` と `trajectreview/` が分離され、raw と派生出力を誤読しない |
| `s16` | `b19`,`b20`,`b21`,`b22` | 後段 handoff | `video.mp4` を含む raw bundle と `session_package.json` / `space_handoff_manifest.json` だけで `SpaceReconstruction` 着手可否と blocker を判断できる |
| `s17` | `b23`,`b24`,`b25`,`b26` | 作業分割 | 補正、モデル生成、レビュー操作を app 単位で分け、各 app が担当段階を明示できる |
| `s18` | `b23`,`b26` | 統合運用 | 統合 app からも同じ workflow を通しで扱え、問題発生時に app 単位で切り分けられる |
| `s19` | `b27`,`b29` | 実データ UX | 各 app が抽出済みまたは modeling 済み bundle を読み、直近実データに基づく状態を表示できる |
| `s20` | `b28`,`b29` | local sample modeling | `Colab` account 未取得でも local sample model と handoff request を生成し、reviewing へ渡せる |
| `s21` | `b30` | correcting 本機能 | `trajectreview-correcting` だけで現場記録開始、停止、session 保存、input export まで進められる |
| `s21a` | `b30a` | correcting data-check | `trajectreview-correcting` が同じ app 内で `data-check` 結果、blocker、recommended correction を返す |
| `s21b` | `b30b`,`b30c`,`b30e` | Google Drive transfer | `trajectreview-correcting` が `data-check` 済み session を 1 件以上選び、`送信Dataset` popup と data 一覧 popup を使って転送対象を確定し、懸念がある data を `▲` 表示したうえで、選択した `Google Drive` 保存場所へ zip を保存できる |
| `s21c` | `b30d` | `DA3` 前段 calibration | `trajectreview-correcting` が `ARCore` frame ごとの camera intrinsics、texture intrinsics、lens distortion、frame timestamp を保存し、後段 `DA3 MetricLarge` へ渡せる |
| `s22` | `b31` | modeling 本機能 | `trajectreview-modeling` だけで `Colab` request、upload 対象、remote result 受理後の package 更新を行える |
| `s22a` | `b31a` | `DA3` depth 基盤 | `DA3Metric-Large` により metric depth 推定と `ARCore pose` / intrinsics 統合の成否、主要指標、失敗理由を route 単位で確認できる |
| `s22b` | `b31a`,`b31b` | route 比較 | 同一 session に対し複数 route を再実行し、sampling、intrinsics、quality、runtime、resource usage、failure reason を同一形式で比較できる |
| `s22c` | `b31b`,`b31c` | route 運用化 | 採用 route と research route が分離され、既定 route を machine-readable に固定できる |
| `s23` | `b32` | reviewing 本機能 | `trajectreview-reviewing` が実 `ReviewArtifact` を開き、経路、同時刻ハイライト、`attention point` を操作できる |
| `s24` | `b33` | gate 運用 | `UX-only`、contract、sample、本機能完成が別 gate として記録され、完了誤認が起きない |

### `MRL` 対応表

- `ux_check_manual_ref` は [ux_check_manual.md](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux_check_manual.md) の章名または操作手順番号をそのまま書く。
- `mrl_ux_valid_ref` は [mrl-ux-valid.md](/Users/tetsuya/kisaragi/kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/mrl-ux-valid.md) の章名をそのまま書く。
- `UX確認待ち` は `ready`、`need`、`done` の 3 値だけを使う。
- `ready` は、system 構築前または構築途中で、まだ admin `UX check` へ出す段階ではないことを示す。
- `need` は、manual、実行環境、対象機能がそろい、admin が今すぐ test できる状態を示す。これは通常 blocker ではない。
- `done` は、admin `UX check` が完了し、結果が `mrl-ux-valid.md` に記録済みであることを示す。
- `未収載` は、まだ `ux_check_manual.md` に具体手順が無いことを明示する。

| MRL | mRL | 目的 | 関連 s-id | 関連 b-id | 現在 gate | UX確認待ち | ux_check_manual_ref | mrl_ux_valid_ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MRL-1` | `-` | 受理と診断の基礎線を成立させる | `s1`,`s2`,`s3` | `b1`,`b2`,`b3`,`b11`,`b13`,`b14` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-1` | `mRL-1.1` | 主入力の受理契約 | `s1` | `b1`,`b11`,`b13` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-1` | `mRL-1.2` | 人物映り込みを含む診断基線 | `s2` | `b2` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-1` | `mRL-1.3` | 実行可否 gate | `s3` | `b3` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-1` | `mRL-1.4` | 分担インターフェース固定 | `s1`,`s12` | `b13`,`b14` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-2` | `-` | 主空間再構成の基礎線を成立させる | `s4`,`s5`,`s6` | `b4`,`b5`,`b6` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-2` | `mRL-2.1` | 主カメラ path と空間基準固定 | `s4`,`s6` | `b4`,`b6` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-2` | `mRL-2.2` | `COLMAP` から `3DGS` への安全 gate | `s5` | `b5` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-2` | `mRL-2.3` | 空間品質要約 | `s6` | `b6` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-3` | `-` | 人物経路再構成と同時刻比較の基礎線を成立させる | `s7`,`s8`,`s9`,`s10` | `b7`,`b8`,`b9` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-3` | `mRL-3.1` | 人物経路の主空間登録 | `s7`,`s9` | `b7` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-3` | `mRL-3.2` | relink と不確実性 | `s7`,`s8` | `b8` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-3` | `mRL-3.3` | 同時刻ハイライトと `attention point` | `s9`,`s10` | `b9` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-4` | `-` | 閲覧成果物と運用硬化を成立させる | `s11`,`s12` | `b10`,`b12`,`b13`,`b14` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-4` | `mRL-4.1` | `ReviewArtifact` と viewer 境界 | `s11` | `b10` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-4` | `mRL-4.2` | 独立 project 境界 | `s12` | `b12`,`b14` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-4` | `mRL-4.3` | 生成物 routing hygiene | `s12` | `b12`,`b13` | `active` | `ready` | `未収載` | `2026-03-25 candidate evidence` |
| `MRL-5` | `-` | correcting の intake / diagnose 基盤を成立させる | `s13`,`s14`,`s15`,`s21` | `b15`,`b16`,`b17`,`b18`,`b30` | `active` | `need` | `操作手順 1-8, pass の判断, fail の判断` | `correcting batch 定義`, `2026-03-25 \`MRL-5\` candidate evidence` |
| `MRL-5` | `mRL-5.1` | legacy alias を含む session source 読込 | `s13` | `b15` | `active` | `need` | `操作手順 1, 6-8` | `2026-03-25 \`MRL-5\` candidate evidence` |
| `MRL-5` | `mRL-5.2` | raw / derived 分離 export | `s13`,`s15` | `b16` | `active` | `need` | `操作手順 6-8` | `2026-03-25 \`MRL-5\` candidate evidence` |
| `MRL-5` | `mRL-5.3` | quality 数値表示付き app UI | `s13`,`s14` | `b17`,`b18` | `active` | `need` | `操作手順 7-8` | `2026-03-25 \`MRL-5\` candidate evidence` |
| `MRL-5` | `mRL-5.4` | correcting 内の現場記録から export までの一連実行 | `s21` | `b30` | `planned` | `ready` | `操作手順 2-8` | `correcting batch 定義` |
| `MRL-5C` | `-` | `trajectreview-correcting` の記録 + data-check を成立させる | `s21`,`s21a`,`s21c`,`s24` | `b30`,`b30a`,`b30d`,`b33` | `active` | `need` | `操作手順 1-8, pass の判断, fail の判断` | `correcting batch 定義`, `2026-03-26 \`MRL-5C\` candidate evidence` |
| `MRL-5C` | `mRL-5C.1` | 記録停止後の最新 session 再読込 | `s21` | `b30` | `active` | `need` | `操作手順 4-6` | `2026-03-26 \`MRL-5C\` candidate evidence` |
| `MRL-5C` | `mRL-5C.2` | app 内 `data-check` artifact 生成 | `s21`,`s21a`,`s21c` | `b30`,`b30a`,`b30d` | `active` | `need` | `操作手順 7-8` | `2026-03-26 \`MRL-5C\` candidate evidence` |
| `MRL-5C` | `mRL-5C.3` | recommended correction 表示 | `s21a` | `b30a` | `active` | `need` | `操作手順 7-8` | `2026-03-26 \`MRL-5C\` candidate evidence` |
| `MRL-5C` | `mRL-5C.4` | calibration capture 診断の切り分け | `s21c`,`s24` | `b30d`,`b33` | `active` | `ready` | `未収載` | `2026-03-28 calibration diagnostic candidate evidence` |
| `MRL-5C` | `mRL-5C.5` | shared camera route の intrinsics 実収集検証 | `s21c`,`s24` | `b30d`,`b33` | `active` | `ready` | `操作手順 11-15, pass の判断` | `2026-03-28 calibration diagnostic candidate evidence` |
| `MRL-5D` | `-` | `trajectreview-correcting` の Google Drive転送を成立させる | `s21b`,`s24` | `b30b`,`b30c`,`b33` | `active` | `need` | `操作手順 10-15, pass の判断, fail の判断` | `correcting batch 定義`, `2026-03-27 \`MRL-5D\` candidate evidence` |
| `MRL-5D` | `mRL-5D.1` | `1 回以上 data-check` 後の転送 gate | `s21b` | `b30b` | `active` | `need` | `操作手順 8-13` | `2026-03-27 \`MRL-5D\` candidate evidence` |
| `MRL-5D` | `mRL-5D.2` | Google Drive への session 転送 | `s21b` | `b30b` | `active` | `need` | `操作手順 10-13` | `2026-03-27 \`MRL-5D\` candidate evidence` |
| `MRL-5D` | `mRL-5D.3` | Drive folder 同期 contract | `s21b` | `b30c` | `active` | `need` | `操作手順 10-13` | `2026-03-27 \`MRL-5D\` candidate evidence` |
| `MRL-6` | `-` | correcting から modeling への concrete handoff を成立させる | `s16`,`s21` | `b19`,`b20`,`b21`,`b22`,`b30` | `active` | `need` | `操作手順 6-12, pass の判断` | `correcting batch 定義`, `2026-03-25 \`MRL-6\` candidate evidence` |
| `MRL-6` | `mRL-6.1` | 主カメラ動画を含む raw bundle 維持 | `s16` | `b19` | `active` | `need` | `操作手順 6-8` | `2026-03-25 \`MRL-6\` candidate evidence` |
| `MRL-6` | `mRL-6.2` | `session_package.json` 正規化 | `s16` | `b20` | `active` | `need` | `操作手順 6-8` | `2026-03-25 \`MRL-6\` candidate evidence` |
| `MRL-6` | `mRL-6.3` | `space_handoff_manifest.json` と UI gate | `s16` | `b21`,`b22` | `active` | `need` | `操作手順 7-8` | `2026-03-25 \`MRL-6\` candidate evidence` |
| `MRL-6` | `mRL-6.4` | correcting export と modeling intake の end-to-end 接続 | `s16`,`s21` | `b30` | `planned` | `ready` | `操作手順 12, 14-15` | `correcting batch 定義` |
| `MRL-7` | `-` | multi-app 骨格と役割境界を成立させる | `s17`,`s18`,`s24` | `b23`,`b24`,`b25`,`b26`,`b33` | `active` | `ready` | `操作手順 1-29, pass の判断, fail の判断` | `reviewing batch 定義`, `2026-03-26 \`MRL-7\` candidate evidence` |
| `MRL-7` | `mRL-7.1` | multi-app module 構成 | `s17`,`s18` | `b23` | `active` | `ready` | `対象, 操作手順 1, 13, 23, 26` | `2026-03-26 \`MRL-7\` candidate evidence` |
| `MRL-7` | `mRL-7.2` | correcting / modeling / reviewing UX 分離 | `s17` | `b24`,`b25`,`b26` | `active` | `ready` | `操作手順 1-29` | `2026-03-26 \`MRL-7\` candidate evidence` |
| `MRL-7` | `mRL-7.3` | 統合 app と app 単位切り分け summary | `s18` | `b26` | `active` | `ready` | `操作手順 26-29` | `2026-03-26 \`MRL-7\` candidate evidence` |
| `MRL-7` | `mRL-7.4` | gate 運用の分離 | `s24` | `b33` | `planned` | `ready` | `未収載` | `reviewing batch 定義` |
| `MRL-8` | `-` | modeling の preflight と remote handoff 準備を成立させる | `s19`,`s20`,`s22` | `b27`,`b28`,`b31` | `active` | `ready` | `操作手順 13-22, pass の判断, fail の判断` | `modeling batch 定義`, `2026-03-26 \`MRL-8\` candidate evidence` |
| `MRL-8` | `mRL-8.1` | 実 bundle 読込 state 再構成 | `s19` | `b27` | `active` | `ready` | `操作手順 13-15` | `2026-03-26 \`MRL-8\` candidate evidence` |
| `MRL-8` | `mRL-8.2` | local sample modeling と Colab handoff request | `s20` | `b28` | `active` | `ready` | `操作手順 14-22` | `2026-03-26 \`MRL-8\` candidate evidence` |
| `MRL-8` | `mRL-8.4` | remote modeling 結果受理前提の package 更新契約 | `s22` | `b31` | `planned` | `ready` | `操作手順 16-22` | `modeling batch 定義` |
| `MRL-9A` | `-` | modeling 比較基盤を成立させる | `s22`,`s22a`,`s24` | `b31`,`b31a`,`b33` | `active` | `ready` | `操作手順 16-22` | `modeling batch 定義` |
| `MRL-9A` | `mRL-9A.1` | `DA3Metric-Large` 前処理入力生成 | `s22a` | `b31a` | `active` | `ready` | `操作手順 19-22` | `modeling batch 定義` |
| `MRL-9A` | `mRL-9A.2` | metric depth 推定と world projection | `s22a` | `b31a` | `planned` | `ready` | `操作手順 21-22` | `modeling batch 定義` |
| `MRL-9A` | `mRL-9A.3` | `Colab` upload manifest と job 実行依頼 | `s22` | `b31` | `active` | `ready` | `操作手順 16-22` | `modeling batch 定義` |
| `MRL-9B` | `-` | modeling の multi-route 比較実験を成立させる | `s22b`,`s24` | `b31a`,`b31b`,`b33` | `active` | `ready` | `未収載` | `modeling batch 定義` |
| `MRL-9B` | `mRL-9B.1` | sampling route 比較実行 | `s22b` | `b31a`,`b31b` | `planned` | `ready` | `未収載` | `modeling batch 定義` |
| `MRL-9B` | `mRL-9B.2` | intrinsics / projection route 比較実行 | `s22b` | `b31b` | `planned` | `ready` | `未収載` | `modeling batch 定義` |
| `MRL-9B` | `mRL-9B.3` | `benchmark_summary.json` 集約 | `s22b` | `b31b` | `active` | `ready` | `未収載` | `modeling batch 定義` |
| `MRL-9C` | `-` | modeling の採用 route 運用化を成立させる | `s22`,`s22c`,`s24` | `b31`,`b31c`,`b33` | `active` | `ready` | `未収載` | `modeling batch 定義` |
| `MRL-9C` | `mRL-9C.1` | `selected_route.json` と default route 固定 | `s22c` | `b31c` | `active` | `ready` | `未収載` | `modeling batch 定義` |
| `MRL-9C` | `mRL-9C.2` | remote result 受理と `SpacePackage` / `TrajectoryPackage` 更新 | `s22` | `b31` | `planned` | `ready` | `未収載` | `modeling batch 定義` |
| `MRL-9C` | `mRL-9C.3` | research route 分離と再実行再現性 | `s22c` | `b31c` | `planned` | `ready` | `未収載` | `modeling batch 定義` |
| `MRL-10` | `-` | reviewing 本機能を成立させる | `s19`,`s20`,`s23`,`s24` | `b29`,`b32`,`b33` | `planned` | `ready` | `操作手順 23-25, pass の判断, fail の判断` | `reviewing batch 定義` |
| `MRL-10` | `mRL-10.1` | reviewing app の実 bundle verify / review summary | `s19`,`s20` | `b29` | `planned` | `ready` | `操作手順 23-25` | `reviewing batch 定義` |
| `MRL-10` | `mRL-10.2` | 実 `ReviewArtifact` loader | `s23` | `b32` | `planned` | `ready` | `操作手順 23-25` | `reviewing batch 定義` |
| `MRL-10` | `mRL-10.3` | same-time highlight と `attention point` 操作 | `s23` | `b32` | `planned` | `ready` | `操作手順 25` | `reviewing batch 定義` |

### INITL 対応表

| INITL | mINITL | 目的 | 関連 MRL / 関連段階 | 現在 gate | UX確認待ち | ux_check_manual_ref | mrl_ux_valid_ref |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `INITL-1` | `-` | `trajectreview-modeling` の `Colab all-in` package 準備を成立させる | `MRL-9A`,`MRL-9B`,`MRL-9C` | `active` | `ready` | `未収載` | `未収載` |
| `INITL-1` | `mINITL-1.1` | `Colab bootstrap package` の source / config / install script 正本化 | `MRL-9A` | `active` | `ready` | `未収載` | `未収載` |
| `INITL-1` | `mINITL-1.2` | `Colab` の account / drive / runtime / install 手順の詳細仕様化 | `MRL-9A`,`MRL-9B` | `planned` | `ready` | `未収載` | `未収載` |
| `INITL-1` | `mINITL-1.3` | zip intake から `session_root/` への unzip / 配置正規化 package | `MRL-9A` | `planned` | `ready` | `未収載` | `未収載` |
| `INITL-2` | `-` | `trajectreview-correcting` の PC install package 準備を成立させる | `MRL-5C`,`MRL-5D`,`MRL-6` | `planned` | `ready` | `未収載` | `未収載` |
| `INITL-2` | `mINITL-2.1` | `correcting` の PC package 構成、install 導線、保存先構成の仕様化 | `MRL-5C`,`MRL-5D` | `planned` | `ready` | `未収載` | `未収載` |
| `INITL-2` | `mINITL-2.2` | PC package と Android app の artifact 互換性と証跡配置の固定 | `MRL-6` | `planned` | `ready` | `未収載` | `未収載` |




## TDD

### 目的文

この章は `prj-kisaragi_0002` の BDD `System Behaviors` を、1 task 1 責務で実装と検証へ落とす。

### TDD タスク

| task_id | behavior_id | test_target | criterion | status | evidence |
| --- | --- | --- | --- | --- | --- |
| `T1` | `b11` | Python session parser alias compatibility | `bt.jsonl` / `poses.jsonl` と `ble_scan.jsonl` / `arcore_pose.jsonl` の両方を 1 parser で読める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `T2` | `b1` | `SessionPackage` intake summary | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、任意入力、時刻基準、品質状態を 1 summary に落とせる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `T3` | `b2` | `Thin Status` diagnose formatter | 人物映り込みの十分性、不足入力、品質、理由を `phase`、`pipeline`、`data_health`、`quality`、`issues` で返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T4` | `b3` | execute readiness gate | 主カメラ動画、主カメラ `IMU`、人物側 `IMU`、空間再構成前提、経路前提がそろわない限り `処理を開始` を返さない | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T5` | `b4` | run phase single-action UX | run phase の `Next Action` が常に 1 件で、現在段階を別 line に出せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T6` | `b5` | `COLMAP` to `3DGS` safety gate | `COLMAP.status != READY_FOR_DENSIFICATION` のとき `3DGS` を開始しない | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T7` | `b6` | `SpacePackage` coordinate contract | 主カメラ path と主空間基準を返し、`GNSS` がない時に主 `ARCore` local 空間を唯一基準として返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T8` | `b7` | `TrajectoryPackage` timeline registration | 主カメラ path、人物 path、不確実性、再拘束点を同じ時刻軸で返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T9` | `b8` | relink uncertainty classifier | visual match confidence、time gap、anchor proximity、`BT` 維持情報で不確実性を決める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T10` | `b9` | verify quality summary | `space` と `trajectory` の quality、同時刻比較の弱点、weak area を同時に返せる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T11` | `b9` | interpret attention point synthesis | `attention point` と同時刻ハイライトに時間範囲、理由、不確実区間情報を持たせる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T12` | `b10` | `ReviewArtifact` boundary contract | `Assembly` だけが `3DGS` 操作、経路表示、同時刻ハイライトを含む `ReviewArtifact` を生成する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T13` | `b12` | independent project boundary scan | `prj-kisaragi_0002` products と docs が外部 project の shared 参照なしで継続できる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py` |
| `T14` | `b12` | output routing hygiene | Android build cache と raw test report が `--exsams`、summary が `--testlogs` に分離される | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/scripts/run_android_unit_tests.ps1` |
| `T15` | `b13` | `InputPackaging` interface manifest | 取得元 raw に加え、受理判定、品質、frame-pose 対応、主体対応表が JSON と CSV の契約で出力される | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `T16` | `b14` | stage handoff contract | 4 分担の各段階で入力、出力、受け渡し条件が文書と実装の両方で読める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py` |
| `T17` | `b15` | session source alias intake | `manifest.json`、`frames.csv`、`bt.csv` を含む legacy alias と、1 段上 parent directory 選択を 1 抽出器で読める | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `T18` | `b16` | raw / derived export bundle | app 抽出が `isensorium/` と `trajectreview/` を分離した bundle を出力する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt` |
| `T19` | `b17` | quality 指標 export | `sensor_quality.json` に時刻整列 delta、completeness score、pose coverage ratio が入る | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt` |
| `T20` | `b18` | extraction UI summary | Android UI が抽出元、抽出先、`ready_for_diagnose`、欠落入力、quality 数値を表示できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `T21` | `b19` | video raw bundle export | app 抽出が `video.mp4` と `video_events.jsonl` を raw bundle に保持する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt` |
| `T22` | `b20`,`b21` | normalized handoff payload | Python parser と Android extractor が `session_package.json` と `space_handoff_manifest.json` を同じ契約で生成する | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py` |
| `T23` | `b22` | space reconstruction gate summary UI | Android UI が `ready_for_space_reconstruction` と blocker を結果画面で返す | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `T24` | `b23` | multi-app module build | `correcting`、`modeling`、`reviewing`、統合 app の 4 module が同じ repository で build できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/settings.gradle.kts` |
| `T25` | `b24`,`b25`,`b26` | role-specific workflow filter | 各 app が自分の役割に対応する workflow 範囲と文言だけを主表示にする | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt` |
| `T26` | `b26` | integrated app overview | 統合 app が 3 app の担当境界を俯瞰表示し、切り分け理由を示せる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `T27` | `b27` | extracted bundle snapshot loader | app が `session_package.json`、`sensor_quality.json`、`space_handoff_manifest.json`、`member_identity_map.json` を読んで実データ state を再構成できる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/WorkflowBundleServiceTest.kt` |
| `T28` | `b28` | local sample modeling output | `modeling` app が `local_model_summary.json`、`colab_job_request.json`、`review_artifact_stub.json` を生成できる | pass | `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/LocalModelingServiceTest.kt` |
| `T29` | `b29` | reviewing actual bundle state | `reviewing` app と統合 app が modeling 結果を読み、verify / review 状態へ反映できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/MainActivity.kt` |
| `T30` | `b30` | correcting end-to-end recording export | `trajectreview-correcting` で現場記録開始、停止、session 保存、input export までを 1 app 内で完了できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `T30a` | `b30a` | correcting data-check service | 最新 session から `sensor_quality.json`、`session_package.json`、`space_handoff_manifest.json`、recommended correction を生成できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/CorrectingDataCheckService.kt` |
| `T30b` | `b30a` | correcting data-check UI | 記録停止後に app 内で readiness、quality、blocker、recommended correction を確認できる | pass | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/res/layout/activity_main.xml` |
| `T30aa` | `b30d` | correcting camera calibration capture | `ARCore` record に `sessionId`、`recordIndex`、`captureTimestampNs`、nested `pose` / `imageIntrinsics` / `textureIntrinsics` / `lensDistortion` を含め、`camera_calibration_summary.json` と `frame_pose_index.csv` を生成できる。`images/` は転送で要求された時だけ生成する | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/RecordingCoordinator.kt` |
| `T30ab` | `b30d`,`b33` | correcting calibration diagnostic separation | `camera_calibration_summary.json` が `読取試行あり成功 0 件`、`calibration export 実装前 data の可能性`、`coverage 低下` を区別して示せる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/CorrectingDataCheckService.kt` |
| `T30ac` | `b30d`,`b33` | shared camera intrinsics acquisition | `corecamera_shared_camera_trial` route の `arcore_pose.jsonl` で `captureDiagnostics.*.requested=true` が出て、intrinsics 未取得なら `request failure` として診断できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/CoreCameraTrialRuntime.kt` |
| `T30c` | `b30b` | correcting Drive transfer gate | `data-check` 済み artifact を持つ selected session が 1 件以上あり、かつ転送先が選択済みなら `転送実行` を許可し、画面直下のコメントで設定済み / 未設定を示せる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `T30d` | `b30b`,`b30c` | Google Drive zip transfer | selected `Google Drive` 保存場所へ、1 件選択時は `<session_id>.zip`、複数件選択時は複数 session を含む zip を作成し、選択した data group だけを zip に含めて保存できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `T30f` | `b30e` | correcting stored session manager | 保存済み session 一覧に取得日時と長さが出て、selected session の再転送と rename ができる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `T30e` | `b30c` | SAF transfer contract | `CreateDocument` で選んだ `Google Drive` 保存場所へ write でき、転送先状態を app 内で設定済み / 未設定として確認できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/correcting/src/main/java/com/isensorium/app/MainActivity.kt` |
| `T31` | `b31a` | `DA3Metric-Large` input manifest | `modeling` app が frame sampling、intrinsics mode、projection option を route 単位で `experiment_manifest.json` と `da3_input_manifest.json` に出力できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `T32` | `b31a` | metric depth runner | `DA3Metric-Large` の少なくとも 1 route を `Colab` で実行し、depth と world projection 用の出力を保存できる | planned | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `T33` | `b31a` | depth estimation report | `metric scale confidence`、`depth continuity`、`point count estimate`、failure reason を `depth_estimation_report.json` に正規化できる | planned | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `T34` | `b31` | colab handoff manifest | `modeling` app が upload 対象、job parameter、result 受理先を machine-readable に出力できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `T35` | `b31b` | sampling route benchmark aggregation | 同一 session に対して複数の sampling route を比較し、quality、runtime、resource usage、failure reason を `benchmark_summary.json` に集約できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `T36` | `b31b` | intrinsics route benchmark aggregation | 少なくとも 2 つの intrinsics / projection route の結果を同一比較表へ集約できる | planned | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `T37` | `b31c` | selected route decision artifact | 暫定採用 route、不採用理由、research route、再評価条件を `selected_route.json` に保存できる | active | `kisaragi-db/--devs/--products/prj-kisaragi_0002/app/src/main/java/com/reviework/app/LocalModelingService.kt` |
| `T38` | `b31` | remote result import | remote modeling 結果を受理し、`SpacePackage`、`TrajectoryPackage`、`modeling_handoff_manifest.json` を更新できる | planned | `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/` |
| `T39` | `b32` | review artifact viewer | `reviewing` app が実 `ReviewArtifact` を読み、viewer と timeline 操作を提供できる | planned | `kisaragi-db/--devs/--products/prj-kisaragi_0002/reviewing/` |
| `T40` | `b33` | gate classification rule trace | `UX-only`、contract、sample、本機能の区別が `b2t`、`mrl-record`、`mrl-ux-valid` で矛盾なく追える | planned | `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/` |

### 実行方針

- `MRL-1` では `T1`、`T2`、`T3`、`T4` を優先し、入口と実行可否 gate を固めた
- `MRL-1` では `T15` と `T16` も先に固め、分担作業の手戻りを防いだ
- `MRL-2` では `T5`、`T6`、`T7` を使って主空間基準と安全 gate を固めた
- `MRL-3` では `T8` から `T11` で人物経路、relink、不確実性、同時刻ハイライト、`attention point` を固めた
- `MRL-4` では `T12` から `T14` で成果物境界と運用 hygiene を固めた
- `MRL-5` では `T17` から `T20` で入力セッション抽出統合、legacy alias intake、bundle 分離、quality 数値表示を固める
- `MRL-5C` では `T30`、`T30a`、`T30b`、`T30aa`、`T30ab`、`T30ac` で `correcting` 単体の記録 + data-check と calibration 診断を固める
- `MRL-5D` では `T30c`、`T30d`、`T30e` で `correcting` 単体の `Google Drive` transfer を固める
- `MRL-6` では `T21` から `T23` で raw video 維持、`SessionPackage` 正規化、`SpaceReconstruction` handoff gate を固める
- `MRL-7` では `T24` から `T26` で 4 app 骨格、role-specific UX、統合 app overview を固める
- `MRL-8` では `T27` と `T28` で実 bundle 読込と local sample modeling を固める
- `MRL-9A` では `T31` から `T34` で `DA3Metric-Large` 前処理、metric depth、`Colab` handoff を固める
- `MRL-9B` では `T35` と `T36` で sampling / intrinsics route 比較を固める
- `MRL-9C` では `T37` と `T38` で採用 route 固定と remote result import を固める
- `MRL-10` では `T29` と `T39` で reviewing 実 bundle summary と実 `ReviewArtifact` viewer を固める

### 現在の見立て

- `T1` から `T16` は、契約実装、project 境界 scan、output routing 実行で `pass` になった
- Python unittest、Android unit test、PowerShell script 実行により、入口契約から成果物 routing までの計画範囲を固定した
- `T17` から `T23` は contract と handoff artifact の基礎は通っているが、`correcting` の本機能 close には未達である
- `MRL-5C` は実装と局所検証が通っているが、`pass` は admin `UX check` batch 実施後に再判定する
- `MRL-5D` は `correcting` の次 gate とし、`現場撮影データ保存 -> data-check -> Google Drive転送` を 1 app UX として閉じる。転送 block 内の順番と popup UX を正本に固定する
- `MRL-5D` の事前設定は `転送先を選択 -> URL を確認または変更 -> 保存先fileを設定する -> Google Drive 上で保存先 file を選ぶ` を既定導線とし、既定 URL は `u/2` の指定 folder に固定する
- `T24` から `T29` は multi-app 骨格、実 bundle summary、`local sample` の検証としては有効だが、本機能完成の証拠としては不十分である
- 次段は `T31` から `T40` を追加し、`DA3Metric-Large` 前処理、multi-route 比較、採用 route 固定、remote result import、実 `ReviewArtifact` viewer、gate 分類を詰める
