# codex-mrl-test-evidence

## 目的文

この文書は `prj-kisaragi_0002` の `MRL` / `mRL` closeout 記録を残す正本とする。

## 記録ルール

- `MRL` または `mRL` が `pass` になったら 1 entry を追加する
- entry には issue、cause、resolution、recurrence prevention、remaining work、evidence path を含める
- planning 基線の再作成や大きな再開判断も entry として残してよい
- `2026-03-29` の再編以後は、現行 gate を `correcting` phase の `MRL-1` と `MRL-2`、`modeling` phase の `MRL-3` から `MRL-7`、および後続 `MRL-**` で読む。再編前 entry は必要に応じて現行対応を本文へ補記する

## Entries

- record date: `2026-03-31`
  target MRL: `MRL-2S`
  target mRL: `mRL-2S.1`、`mRL-2S.2`
  gate change: `active`
  issue: `通常計測` の長時間収録は screen off 抑止だけでは閉じず、`1min15s` 前後で app crash が起きていた
  cause: 実機 crash log で `isensorium-shared-camera-trial` thread の `OutOfMemoryError` を確認した。`TrialCpuImageVideoRecorder` が収録中の全 YUV frame を RAM に保持し、停止時にまとめて encode していた
  resolution: `MainActivity` 側で keep-awake を追加済みの前提で、`TrialCpuImageVideoRecorder` を逐次 encode 方式へ変更し、収録中に `MediaCodec` / `MediaMuxer` へ流し込む構成へ切り替えた。frame をメモリへ蓄積しないため、長時間側は frame drop 許容で連続稼働を優先する
  recurrence prevention: `correcting` の長時間収録問題は screen off と crash を分離して扱い、実機 crash 時は `exit-info` と crash buffer を必ず取得してから route 切替や sampling 仮説へ進む
  remaining work: 修正 build を実機で `10min` 収録し、落ちないこと、session が `finalized` になること、`video.mp4` が残ることを admin 手順で確認する
  evidence path: `kisaragi-db/--exsams/prj-kisaragi_0002/device-debug/`

- record date: `2026-03-31`
  target MRL: `MRL-2S`
  target mRL: `mRL-2S.2`
  gate change: `active`
  issue: `OOM` 修正後の `2min30s` 実収録では crash しなくなったが、`撮影停止` 後に session が `recording` のまま止まり、停止処理が完了しなかった
  cause: 実機 session `session-20260331-044636` では `video.mp4` が `26MB` まで伸びていた一方、`session_manifest.json` は `status=recording` のまま、`video_events.jsonl` も空だった。`TrialCpuImageVideoRecorder.finishEncoding()` は `MediaCodec.INFO_TRY_AGAIN_LATER` が続いた時に終端 drain の抜け条件がなく、`stopAndRelease()` が無限待ちになる経路を持っていた
  resolution: `CoreCameraTrialRuntime.kt` の `drainCodec(endOfStream=true)` に `5s` の `STOP_DRAIN_TIMEOUT_NS` を追加し、`EOS` が返らない時は timeout で抜けて finalize を進める bounded stop に変更した
  recurrence prevention: 停止不良は `video.mp4` の成長有無、`session_manifest.json` の `status`、`video_events.jsonl` の有無を同時に見て、crash と finalize hang を分離して扱う
  remaining work: bounded stop 版を実機へ入れ直し、`2min30s` 以上と `10min` の両方で `撮影停止` 後に session が `finalized` まで進むかを admin 手順で確認する
  evidence path: `kisaragi-db/--exsams/prj-kisaragi_0002/device-debug/`

- record date: `2026-03-29`
  target MRL: `MRL-1`、`MRL-2`
  target mRL: `mRL-1.1` から `mRL-1.3`、`mRL-2.1` から `mRL-2.3`
  gate change: `p-done`
  issue: `correcting` 側は実データ取得と `Google Drive` 転送を完了し、その data が `MRL-5` の `3DGS` smoke 生成へ実際に使われていたが、gate 表では `active` / `ready` が多く残っていた
  cause: `candidate evidence` は個別に蓄積されていた一方で、`correcting -> modeling` handoff 実績をまとめて `p-done` 判定へ昇格する close 記録が不足していた
  resolution: `MRL-1` と `MRL-2` を、実 session 記録、`data-check`、calibration 診断、`Google Drive` 転送、`session_package.json` / `space_handoff_manifest.json` による handoff bundle 生成、さらにその転送済み data が `MRL-5` で実利用された事実を根拠に `p-done` へ更新した
  recurrence prevention: `correcting` 側の実データ取得と転送が後段 gate の実行証跡へ接続した時は、個別 candidate evidence のまま残さず、前段 gate 群をまとめて `p-done` 判定へ引き上げる
  remaining work: `MRL-3` 以降の `modeling` を継続し、reviewing viewer や multi-app 統合は後続 `MRL-**` で扱う
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`

- record date: `2026-03-29`
  target MRL: `MRL-3`、`MRL-4`、`MRL-5`、`MRL-6`
  target mRL: `mRL-3.1`、`mRL-4.1`、`mRL-4.2`、`mRL-5.1`、`mRL-5.2`、`mRL-5.3`、`mRL-6.1`、`mRL-6.2`
  gate change: `p-done`
  issue: `modeling` の bootstrap、preflight、single-frame smoke、evidence bundle 取得が別番号に分散していたため、どこまでを完了済みとみなすかが曖昧だった
  cause: `3DGS` 系 smoke artifact と local downloaded evidence が揃った後も、phase 単位の完了範囲と次段の焦点を更新し切れていなかった
  resolution: `MRL-3` を bootstrap / install、`MRL-4` を bundle 読込 / request preflight / directory intake、`MRL-5` を single-frame `3DGS` smoke、`MRL-6` を product 側 evidence bundle 取得として再整理し、ここまでを `p-done` へ更新した。`10s` 前後の整った実動画を使う `multi-frame` densify と `ぼんやり見える再現モデル` の確認は `MRL-7` へ移した
  recurrence prevention: stage が切り替わる時は、evidence 追加だけで終わらせず、`ux-b2t-hypo.md` の gate 状態、次段の焦点、補助再開メモを同じ task で更新する
  remaining work: `MRL-7` として `multi-frame` densify と `PLY` viewer での可視化確認へ進み、route 比較と `selected_route.json` 生成は後続の利用者向け `MRL-**` に紐づく補助 gate で扱う
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/evidence/da3_smoke_v05/`

- record date: `2026-03-29`
  target MRL: `MRL-5`
  target mRL: `mRL-5.2`、`mRL-5.3`
  gate change: `candidate evidence strengthened`
  issue: `MRL-5` は depth bootstrap までは通っていたが、`correcting` 実 data から `3DGS` 系主空間モデル候補を再現できるか、また smoke artifact を `SpacePackage` 形へ接続できるかが未記録だった
  cause: 初期 closeout は single-frame depth bootstrap の成立確認を優先し、world projection、point export、`gsplat` rasterization、contract artifact 生成の結果を正本へ昇格し切れていなかった
  resolution: `DA3Metric-Large` single-frame depth、world back-projection、point export、`gsplat` rasterization、`gs_model_smoke.json`、`space_quality_smoke.json`、`space_package_smoke.json`、contract 名 artifact 生成までを `Candidate Bootstrap v1` と `admin-mrl-test-evidence.md` へ反映し、`MRL-5` の candidate proof を「correcting 実 data から `3DGS` 系主空間モデル候補を再現できる」水準まで引き上げた
  recurrence prevention: Colab 往復で得た持続価値のある結果は、shared worklog のみへ残さず、runbook、admin evidence、必要なら closeout 記録へ同じ task で反映する
  remaining work: `admin-mrl-test-evidence.md` を根拠に `MRL-5 p-done` 判定を行うか判断し、後続 gate では `trajectreview-modeling` 正式統合と `multi-frame` / `multi-route` を別 MRL として進める
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md`

- record date: `2026-03-30`
  target MRL: `MRL-7`
  target mRL: `mRL-7.1`
  gate change: `p-done`
  issue: `MRL-7` は `TraceCore` multi-frame visible reconstruction を主 target にしていたが、shared log にしか進捗が無く、`active` の中身が正本から読めなかった
  cause: fresh runtime からの再立ち上げ、window 探索、depth batch、world fusion、preview closeout を優先し、`admin-mrl-test-evidence.md` と `ux-b2t-hypo.md` への反映が後ろにずれていた
  resolution: 実 session の最長連続 window 約 `3.95s` を正として sampled `12 frame` の depth batch を実行し、`11 frame` / `3696 points` の multi-frame world fusion、`world_points_multiframe_preview.png`、`mrl7_closeout_summary.json` を保存した。この範囲を `mRL-7.1` として切り出し `p-done` に上げ、`PLY` viewer 目視確認と人軌跡重畳を含む最小表示は `mRL-7.2` へ分離した
  recurrence prevention: `MRL-7` 以降の Colab 往復では、shared worklog の step 成功ごとに、どこまでをその `mRL` の成立範囲に含めるかを同日中に正本へ固定する
  remaining work: `mRL-7.2` として `PLY` viewer での目視確認、人軌跡重畳を含む `TraceCore` 最小表示、全体俯瞰 / 時系列 / 相対表示 / 滞留 / 交錯の価値確認を進める
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`

- record date: `2026-03-30`
  target MRL: `MRL-7`
  target mRL: `mRL-7.2`
  gate change: `p-done`
  issue: `正規 gaussian parameter の生成と最適化` を始める前は、点群と smoke render までしかなく、`3DGS` 本体へ入れたとは言いにくかった
  cause: point cloud と `gsplat.rasterization` smoke を先行して成立させた一方、gaussian parameter の tensor 初期化、backward、短い optimization loop の確認が未着手だった
  resolution: multi-frame point cloud から gaussian parameter を初期化し、`gsplat` 上で `1 step` probe と `20 step` の短い optimization を通した。`loss_init = 0.18226878345012665` から `loss_final = 0.035895735025405884` まで低下し、`gaussian_params_init.pt`、`gaussian_params_optim20.pt`、`gaussian_render_init.png`、`gaussian_render_optim20.png` を保存した。さらに `500 step` と `2500 step` の拡張 optimization も実行し、`2500 step` 版では `loss_final = 0.009165632538497448` まで低下、admin の目視で `gaussian_render_optim2500.png` が「かなり再現されている」「取得背景に近い構図」と確認できたため、この範囲を `mRL-7.2 p-done` とした
  recurrence prevention: Colab 上で `3DGS` 本体へ進む時は、最初に `1 step` backward probe を通し、引数 shape や path 解決を潰してから短い optimization loop と目視確認へ進む
  remaining work: viewer で読む正式 gaussian scene 形式の固定、artifact download の標準化、multi-view 条件の拡張、人軌跡重畳を含む `TraceCore` 最小表示は後続 `MRL-**` で進める
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`

- record date: `2026-03-31`
  target MRL: `MRL-8`
  target mRL: `mRL-8.1`、`mRL-8.2`
  gate change: `p-done`
  issue: `DA3 Colab` runbook は特定 zip path を hardcode しており、fresh runtime で別 session を試すたびに手編集が必要だった
  cause: input candidate scan は文字列 path ベースで重複し、`shortcut-targets-by-id` と `MyDrive` の同一実体 zip を canonical に 1 件へ寄せられていなかった。また selected input を runbook 本体と `MRL-7` one-block の両方へ handoff する closeout が未記録だった
  resolution: candidate scan を `session_id + size_bytes` と path rank で canonical 化し、widget で selected input を保存する前段を runbook 正本へ組み込んだ。admin は `[2] trajectreview-correcting-session-20260331-034831 [zip]` を選択し、`Step 8d` で `Step 2` から `Step 4.5`、`Step 8e` で `MRL-7 adopted one-block` を同じ input から end-to-end で実行できた
  recurrence prevention: Drive mount で同一実体が複数 path に見える時は `resolve()` だけに頼らず、session-level key と優先順位で canonical candidate list を作ってから widget UX を確定する
  remaining work: `MRL-8` で確立した selected input handoff を、後続 `job_status.json`、request UX、result download、viewer formalization へ接続する
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md`

- record date: `2026-03-26`
  target MRL: `旧番号時代の全 gate`
  target mRL: `current pass entries all`
  gate change: `reverted to active/planned`
  issue: admin `UX check 完了` 前でも、test、contract、build、local sample、局所 device 確認を根拠に `pass` を付けていた
  cause: `pass` の必須条件として admin `UX check` と batch check 運用を shared rule へ明文化していなかった
  resolution: `AGENTS.md`、`ux-b2t-hypo.md`、関連 admin test 文書を更新し、`MRL` 記載順を運用順 `correcting -> modeling -> reviewing` に統一し、admin `UX check` 未完の gate を `active` / `planned` へ戻した
  recurrence prevention: 以後の `pass` は admin `UX check 完了` が記録された gate のみに付与し、関連 gate は batch でまとめて確認範囲を記録する
  remaining work: admin 向け batch `UX check` の対象範囲、手順、結果記録を `admin-mrl-test-evidence.md` へ追加し、各 gate を再 closeout する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md`
- record date: `2026-03-26`
  target MRL: `MRL-1`
  target mRL: `mRL-1.1`、`mRL-1.2`、`mRL-1.3`
  gate change: `pass`
  issue: `trajectreview-correcting` は記録画面だけで、同じ app 内の `data-check` と correction guidance が不足していた
  cause: `correcting` は verified mirror の recording screen に依存しており、session 停止後の intake / diagnose を app 内で閉じていなかった
  resolution: `CorrectingDataCheckService` を追加し、最新 session 再読込、`sensor_quality.json`、`session_package.json`、`space_handoff_manifest.json` 生成、recommended correction 表示を `correcting` 内へ実装した
  recurrence prevention: `correcting` の gate は記録画面だけで close せず、実 session から derived artifact が生成され、app 上に correction guidance が表示されるまで `pass` にしない
  remaining work: `modeling` 側の `Colab` handoff と `reviewing` 側の実 `ReviewArtifact` viewer を継続する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`
- record date: `2026-03-26`
  target MRL: `旧番号時代の correcting / modeling / multi-app 補助 gate`
  target mRL: `旧番号時代の sample / build / summary 系 mRL`
  gate change: `reverted to active/planned`
  issue: `UX 確認`、`build / install`、`local sample`、summary 読込を本来機能完成に近い意味で扱い、app の完成度を過大に closeout していた
  cause: `UX-only` gate と本機能 gate を分離せず、multi-app 骨格と実 app 機能の境界を `MRL` 表へ十分に反映していなかった
  resolution: `ux-b2t-hypo.md` と `project-truth.md` を再設計し、correcting、modeling、reviewing、統合 app の完成条件を本来機能基準へ引き直し、該当 gate を `active` / `planned` へ戻した
  recurrence prevention: mock、stub、sample、contract、build / install は補助 gate として別扱いにし、本機能 `pass` は実入出力と実生成物の end-to-end 証跡がある時だけ付与する
  remaining work: `correcting` の end-to-end、`Colab` handoff、remote result import、実 `ReviewArtifact` viewer、統合 app の end-to-end を実装する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md`
- record date: `2026-03-25`
  target MRL: `none`
  target mRL: `none`
  gate change: `initialized`
  issue: `trajectreview` の再開前提が外部一時文書に残っており、削除後に計画根拠を失う状態だった
  cause: 処理 4 段階、`GNSS` なし前提、UX 概念、package 契約が `prj-kisaragi_0002` の正本文書へ十分に吸収されていなかった
  resolution: `project-truth.md` と計画正本を更新し、再開基線を `prj-kisaragi_0002` 配下へ集約した
  recurrence prevention: 外部補助文書で採用した構想は、次の実装着手前に `project-truth` と BDD / TDD 正本へ同時反映する
  remaining work: 契約 closeout を実データ処理と viewer 実装へ接続する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md`
- record date: `2026-03-25`
  target MRL: `MRL-1`
  target mRL: `mRL-1.1`、`mRL-1.4`
  gate change: `pass`
  issue: 受理契約と分担インターフェースの入口固定が未完だった
  cause: parser と controller が静的 demo 中心で、人物映り込みや readiness を判定する契約評価が未固定だった
  resolution: Python parser に `SessionPackage` インターフェース出力を追加し、入力契約と段階間インターフェースを test で固定した
  recurrence prevention: 新しい入力契約は parser test と controller test の両方で固定する
  remaining work: diagnose と execute gate を `active` で継続し、実データ入力を Android UI へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_session_parser.py`
- record date: `2026-03-25`
  target MRL: `MRL-2` から `MRL-4`
  target mRL: `mRL-1.2`、`mRL-1.3`、`mRL-2.x`、`mRL-3.x`、`mRL-4.x`
  gate change: `reverted to active/planned`
  issue: 契約 test と文書整合だけで `pass` 扱いしたため、着手中と完了済みの境界を取り違えた
  cause: `planned`、`active`、`pass` の運用意味を文書へ明文化する前に、契約固定済み項目を一括 closeout してしまった
  resolution: `AGENTS.md` に状態語の意味を追加し、計画正本の gate を保守的に `active` / `planned` へ修正した
  recurrence prevention: `MRL` / `mRL` の closeout は、実装、検証、残作業の 3 点がそろった項目だけに限定する
  remaining work: 実データ接続、viewer 実装、生成物 routing を継続し、`active` と `planned` を順次 close する
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/ux-b2t-hypo.md`
- record date: `2026-03-25`
  target MRL: `MRL-1`
  target mRL: `mRL-1.2`、`mRL-1.3`
  gate change: `pass`
  issue: diagnose と execute gate が contract demo 止まりで、完了扱いに戻せていなかった
  cause: 状態語修正後に、再評価済み evidence を gate 表へ戻していなかった
  resolution: Kotlin controller / unit test を evidence として再評価し、diagnose と execute readiness gate を `pass` に戻した
  recurrence prevention: 状態語訂正時も、有効な evidence を持つ task は再 closeout する
  remaining work: 実データ pipeline への接続
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-2`
  target mRL: `mRL-2.1` から `mRL-2.3`
  gate change: `pass`
  issue: 主空間基準、安全 gate、品質要約が契約固定済みでも closeout 未反映だった
  cause: 状態語見直し時に保守的に `active` へ戻した後、再判定を保留していた
  resolution: `SpacePackage` 関連の controller test を再評価し、`COLMAP` safety gate と coordinate contract を `pass` に更新した
  recurrence prevention: `MRL` closeout は TDD `pass` 一覧と突き合わせて更新する
  remaining work: 実空間再構成 engine との接続拡張
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-3`
  target mRL: `mRL-3.1` から `mRL-3.3`
  gate change: `pass`
  issue: 人物経路、不確実性、同時刻ハイライトが closeout 未反映だった
  cause: trajectory contract の実装と test は存在したが、状態訂正後に再 closeout していなかった
  resolution: relink、不確実区間、same-time highlight、attention point を Kotlin test evidence として再評価し、`pass` に更新した
  recurrence prevention: trajectory 系は同一 test file の pass 状態を `MRL` 表へ反映する
  remaining work: 実データ由来 path の拡張
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ReviewScreenControllerTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-4`
  target mRL: `mRL-4.1` から `mRL-4.3`
  gate change: `pass`
  issue: stage handoff contract、独立運用 scan、output routing hygiene の完了証跡が不足していた
  cause: docs のみで管理していたため、project 境界と routing の自動検査がなかった
  resolution: `review_contracts.py` と `test_project_contracts.py` を追加し、`run_android_unit_tests.ps1` と `run_python_tests.ps1` を `--exsams` / `--testlogs` 分離運用へ更新した
  recurrence prevention: handoff contract と routing は code と script 実行結果の両方を evidence にする
  remaining work: 実 viewer への contract 接続拡張
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/test_project_contracts.py`
- record date: `2026-03-25`
  target MRL: `MRL-5`
  target mRL: `mRL-5.1` から `mRL-5.3`
  gate change: `pass`
  issue: `trajectreview` が UI mock のままで、入力セッション folder から raw と追加出力を app 自身では取り出せなかった
  cause: `InputPackaging` は Python parser 契約までは固定済みだったが、Android app 側に source 選択、export、quality summary の導線がなかった
  resolution: Kotlin extractor を追加し、legacy alias intake、`isensorium/` と `trajectreview/` の分離 export、quality 数値表示付き UI、Python / Android test を実装した
  recurrence prevention: `InputPackaging` の route 変更は、parser 互換 test、Android export test、UX manual を同じ task で更新する
  remaining work: 抽出 bundle を後段の実空間再構成と viewer 実装へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt`
- record date: `2026-03-25`
  target MRL: `MRL-2`
  target mRL: `mRL-2.3`
  gate change: `pass`
  issue: 抽出 bundle は生成できても、`SpaceReconstruction` がそのまま消費できる concrete handoff artifact と主カメラ動画保持が不足していた
  cause: `MRL-5` までは intake と quality summary を優先し、`SessionPackage` 実体と stage-2 gate を抽象契約のまま残していた
  resolution: `video.mp4` と `video_events.jsonl` を raw bundle に含め、`session_package.json`、`space_handoff_manifest.json`、space gate 表示を Python / Android の両方へ実装した
  recurrence prevention: 後段 stage の abstract contract を追加した時は、同じ session で concrete artifact 名、UI summary、Python validator をそろえる
  remaining work: `space_handoff_manifest.json` を実 `SpaceReconstruction` engine の入口へ接続する
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/ISensoriumExtractionServiceTest.kt`
- record date: `2026-03-26`
  target MRL: `MRL-**`
  target mRL: `mRL-**.5`
  gate change: `pass`
  issue: 4 app 分割の骨格は入ったが、build、install、role-specific UX の成立を closeout できていなかった
  cause: module 追加と共通 source 再利用までは進んでいた一方、統合 app との関係と app 単位切り分け表示の evidence が不足していた
  resolution: `correcting`、`modeling`、`reviewing`、統合 app の 4 module を build / install し、role-specific workflow 表示と担当境界 summary を controller / activity へ実装した
  recurrence prevention: multi-app 導入時は module build、unit test、device install、役割表示を同じ gate で closeout する
  remaining work: 実 bundle 読込と local modeling による mock 依存の解消
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/settings.gradle.kts`
- record date: `2026-03-26`
  target MRL: `MRL-3`
  target mRL: `mRL-3.1` から `mRL-3.2`
  gate change: `pass`
  issue: 4 app が mock snapshot 固定だと、実データでの UX 確認と `Colab` 前提 modeling handoff を進められなかった
  cause: extracting 後の bundle を再読込する service と、`Colab` account 未取得期間の local sample modeling route が未実装だった
  resolution: `WorkflowBundleService` で実 bundle から state を再構成し、`LocalModelingService` で `local_model_summary.json`、`colab_job_request.json`、`review_artifact_stub.json` を生成し、4 app すべてで実データ UX を使えるようにした
  recurrence prevention: 実データ UX が必要な段階は mock snapshot だけで closeout せず、bundle reader、生成 artifact、reviewing 側読込の 3 点を必須とする
  remaining work: `colab_job_request.json` を実 `Colab` 実行へ接続し、sample output を本物の `3DGS` 成果物へ置き換える
  evidence path: `kisaragi-db/--devs/--testcode/prj-kisaragi_0002/android-test/java/com/reviework/app/WorkflowBundleServiceTest.kt`
- record date: `2026-03-31`
  target MRL: `MRL-9`
  target mRL: `mRL-9.1`
  gate change: `p-done`
  issue: `DA3 Giant` の Gaussian branch は docs 上の route が見えていても、実行 method、`e3nn` 依存、保存先 contract が未固定で、`gs_ply` / `gs_video` 出力まで到達できていなかった
  cause: 初回 block では `DepthAnything3.infer(...)` を想定していたが、実 method は `inference(...)` だった。また `e3nn` install 後に stale import が残り、`matrix_to_angles` 未定義で落ちていた
  resolution: `Step 9d` で repo docs / API を再探索し、`da3-giant` + `infer_gs=True` + `export_format=\"npz-glb-gs_ply-gs_video\"` を固定した。`e3nn` install を `DepthAnything3` import 前へ移し、module reload 後に `inference()` を再実行して `gs_ply/0000.ply`、`gs_video/0000_extend.mp4`、`scene.glb`、`exports/npz/results.npz` の生成に成功した
  recurrence prevention: `MRL-9` を統合済みの main runbook pair では、`e3nn` install を import 前に置く。Gaussian branch failure では dependency 追加後の stale import を疑い、module reload または fresh import 順を先に確認する
  remaining work: `mRL-9.2` として `gs_ply` を `SuperSplat` または `PlayCanvas Model Viewer` で開き、自由視点 scene として読めることを admin evidence 化する
  evidence path: `kisaragi-db/--devs/--products/prj-kisaragi_0002/modeling/da3_colab_evid_runbook.md`
- record date: `2026-03-31`
  target MRL: `MRL-9`
  target mRL: `mRL-9.2`
  gate change: `p-done`
  issue: `gs_ply` が生成できても、外部 viewer で自由視点 scene として読めるかが未確認だった
  cause: `mRL-9.1` は Colab export までを閉じており、viewer 側の admin UX 確認を別 gate に分けていた
  resolution: `gs_ply/0000.ply` を `PlayCanvas Model Viewer` に読み込み、自由視点 scene として表示されることを admin が確認した
  recurrence prevention: `gs_ply` route を close する時は、export 成功だけでなく viewer 側の opening evidence も同じ日付で残す
  remaining work: top camera renderer、path overlay、request / status UX は後続 `MRL-**` へ送る
  evidence path: `kisaragi-db/--devs/--tgpce-map/prj-kisaragi_0002/admin-mrl-test-evidence.md`
