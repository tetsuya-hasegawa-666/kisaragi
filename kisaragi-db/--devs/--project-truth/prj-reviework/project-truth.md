# project-truth

この文書は `prj-reviework` の artifact 正本を統合した `project-truth.md` とする。

## 目的

`reviework` は、現場で収録された画像・センサ群から reconstruction pipeline を起動し、空間再構成と行動軌跡を同一 timeline 上で束ねた review workspace を提供する project とする。

## north star

- user は「今なにをすべきか」で迷わない
- user は pipeline の状態と異常理由を薄く常時把握できる
- user は review 結果から次の判断へ進める
- `Next Action` は常に 1 件だけ提示する
- `Thin Status` は 3 から 6 項目で状態、品質、issue を最小表示する

## user value

- 作業空間を 3DGS ベースで理解できる
- 人や物の行動軌跡を timeline で追える
- quality 低下や reconstruction failure の理由が短く分かる
- review すべき attention point が自動で絞られる

## UX 原則

- `Next Action` は一意提示とし、処理中でも action 名と state message を分けて表示する
- `Thin Status` は常時表示とし、正常時は薄く、異常時のみ強調する
- user に探索を強要せず、review に必要な attention point を先回りして提示する
- `Timeline` を全データ統合キーとし、space、trajectory、attention point を同一 artifact に束ねる

## UX フェーズ

### Intake

- 目的: data folder を受け取り、session として受理する
- 主表示: データフォルダを選択
- 状態表示: frame 数、必須入力の欠落有無

### Diagnose

- 目的: 処理可否と入力品質を判定する
- 主表示: 実行する / 修正する
- 状態表示: data health、主要 issue、修正理由

### Run

- 目的: pipeline を実行する
- 主表示: 完了を待つ
- 状態表示: 現在ステップ、進行率、blocking issue

### Verify

- 目的: reconstruction と trajectory の成立品質を確認する
- 主表示: 結果を確認
- 状態表示: 空間品質、軌跡品質、弱点

### Interpret

- 目的: review と改善判断を行う
- 主表示: この区間を見る
- 状態表示: 重要イベント、不確実区間、attention point

## project contract

### required inputs

- session directory または同等の input package
- `frames`
- `imu`
- `bt`
- optional `poses`
- optional `gnss`
- session-level `timebase`
- quality / metadata fields

### required outputs

- `SessionPackage`
- `SpacePackage`
- `TrajectoryPackage`
- `Timeline`
- `ReviewArtifact`
- pipeline progress と issues を含む `Thin Status`
- user に 1 つだけ提示する `Next Action`

### bootstrap phase の非目標

- `COLMAP` / `3DGS` 実行 engine 本体の内製実装
- final 3D viewer の高忠実度描画
- Android app 内での heavy reconstruction 実行
- `iSensorium` 側の package 名や file を shared 参照のまま残す運用

## system blueprint

### pipeline shape

```text
Input
-> Preprocess
-> COLMAP
-> 3DGS
-> Trajectory
-> Assembly
-> Viewer
```

### module responsibility

- `InputPackaging`: sensor 統合、timebase 正規化、`SessionPackage` 生成
- `Preprocess`: frame thinning、blur / duplicate / dark frame 除外、diagnose summary 生成
- `COLMAP`: valid frame set 確定、camera pose 推定、sparse reconstruction 成立判定
- `3DGS`: scene representation 生成、viewer 向け表現 package 出力
- `Trajectory`: entity path 推定、relink、uncertainty 付与
- `Assembly`: `SpacePackage`、`TrajectoryPackage`、`Timeline` を統合し `ReviewArtifact` を生成
- `Viewer`: 生成済み artifact を読む read-only review 面

### data structures

- `SessionPackage`: `frames`、`imu`、`bt`、optional `poses` / `gnss`、`quality`、`timebase`
- `SpacePackage`: `coordinate_system`、`camera_path`、`sparse_points`、`gs_model`
- `TrajectoryPackage`: `entities`、`anchors`、`relinks`、`uncertainty`、`space_ref`
- `Timeline`: `timestamps`、`mapping`
- `ReviewArtifact`: `space`、`trajectory`、`timeline`、`attention_points`、`summary`、`entrypoint`

## reuse boundary

### `iSensorium` から流用するもの

- session manifest / CSV / JSONL を読む parser 形状
- monotonic timebase を中心にした timeline 統合
- issue severity と suggested action の軽量提示
- Android の単画面 control panel 骨格

### `reviework` 固有責務

- `COLMAP`、`3DGS`、`Trajectory`、`Assembly` の pipeline 契約
- review 用の `Next Action + Thin Status` UX
- `ReviewArtifact` の生成と `Viewer` への受け渡し

## 設計補正

- `gnss` は fixed field ではなく optional input とする
- `Thin Status` の UI 表示カテゴリは `phase`、`pipeline`、`data_health`、`quality`、`issues` の 5 項目に固定する
- `3DGS` は `COLMAP.status == READY_FOR_DENSIFICATION` のときのみ開始可能とする
- `relink` は visual match confidence、time gap、anchor proximity の 3 条件で判定する
- `Assembly` を唯一の `ReviewArtifact` 生成者とし、`Viewer` は read-only 消費者とする

## 成功条件

- 迷わない
- 状態が分かる
- 理由が分かる
- 次の判断ができる
