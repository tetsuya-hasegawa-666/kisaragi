# 2026-03-22-007 micro release lines

## 現在状態

- all micro releases in this plan set are `completed`
- release-line の附番は `2026-03-25` の今回修正開始を `MRL-1` / `mRL-1-1` の起点として読み替える
- この文書は `hi-ai-unified-blueprint.md` と `hi-ai-unified-blueprint.md` を補助する参考情報である
- `prj-kisaragi_0001` は `codev-viewer` の実装資産を基底に再構成した project として記録する

## MRL-1 source profile foundation line

### mRL-1-1 source profile manifest contract

- status: `completed`
- 目標:
  - `db-view` と `prj-view` を profile 単位で表現する manifest contract を定義する
  - configured roots 外アクセスを拒否する read-only policy を維持する
  - failing test の入口を `liveProjectSnapshot` 系へ置く

### mRL-1-2 shell switch and read-only reset

- status: `completed`
- 目標:
  - shell で active profile を切り替えられる
  - 切替時に lane 候補と explorer state が更新される
  - edit / draft / apply 系 UI を撤去する

### mRL-1-3 documentation and state alignment

- status: `completed`
- 目標:
  - profile switch baseline を current state / evidence / history へ反映する
  - foundation line 完了後も UI 方針が未確定であることを明記する

## MRL-2 comparison workspace line

### mRL-2-1 compare lane selection model

- status: `completed`
- 目標:
  - 2 lane 以上の compare selection を controller / model で固定する
  - lane は profile と document path を保持する

### mRL-2-2 side-by-side preview contract

- status: `completed`
- 目標:
  - lane ごとに title / profile / path / body を比較表示する
  - compare empty / mismatch / missing を view contract で分離する

### mRL-2-3 cross-profile comparison evidence

- status: `completed`
- 目標:
  - 異なる profile の文書比較が成立することを test と UX note で固定する

## MRL-3 local handoff line

### mRL-3-1 reveal target resolution

- status: `completed`
- 目標:
  - file と directory の reveal target を configured roots 制約つきで解決する
  - roots 外 path は拒否する

### mRL-3-2 right click Explorer handoff

- status: `completed`
- 目標:
  - 名称の context action から Explorer handoff を呼べる
  - handoff failure は operator-facing message で見える

### mRL-3-3 no-edit UX close

- status: `completed`
- 目標:
  - in-app editing を持たない方針を UI と docs の両方で固定する
  - 利用者が local editor へ移る導線を completed とする

## MRL-4 launch and UI direction line

### mRL-4-1 launch method candidates

- status: `completed`
- 目標:
  - entry command 候補を比較し、foundation 後の妥当な起動方法を決める

### mRL-4-2 global UI composition direction

- status: `completed`
- 目標:
  - navigator / compare lane / metadata / action の全体構成を 1 本に定める

### mRL-4-3 implementation-start close

- status: `completed`
- 目標:
  - UI 方針を current state / history / evidence に反映し、実装 line を開始可能にする

