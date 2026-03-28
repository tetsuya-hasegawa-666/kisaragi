# 2026-03-22-007 market release lines

## 目的

`2026-03-22-007` は、`iDevelop` を `prj-isensorium` 固定の consultation/archive viewer から、`db-view` と `prj-view` を切り替える read-only comparison viewer へ再設計する plan set とする。

## 位置付け

- この文書は `ux-b2t-hypo.md` と `ux-b2t-hypo.md` を補助する参考情報である。
- release-line の附番は `2026-03-25` の今回修正開始を `MRL-1` の起点として読み替える。
- `prj-kisaragi_0001` は `codev-viewer` の実装資産を基底に再構成した project として記録する。

## planning rule

- `MRL-1` から `MRL-3` までは foundation line とする
- 起動方法と UI 全体構成は foundation line が閉じるまで仮決めしない
- `MRL-4` は foundation 後に entry command と UI 全般方針を定義する line とする

## market release lines

| ID | name | 提供価値 | status |
|---|---|---|---|
| MRL-1 | source profile foundation line | `db-view` / `prj-view` を切り替える manifest と shell baseline を確立 | completed |
| MRL-2 | comparison workspace line | cross-profile document compare lane と read-only preview baseline を確立 | completed |
| MRL-3 | local handoff line | right click Explorer handoff と no-edit UX baseline を確立 | completed |
| MRL-4 | launch and UI direction line | 起動方法と UI 全体構成を foundation 後に定義 | completed |

## 完了条件

- `MRL-1`
  - source profile manifest contract が test で固定される
  - shell で active profile を切り替えられる
  - edit / draft / apply が UI から消える
- `MRL-2`
  - compare lane に文書を固定できる
  - 異なる profile の文書を同時に比較できる
  - compare empty / mismatch state を区別して示せる
- `MRL-3`
  - reveal target contract が roots 制約つきで固定される
  - right click から Explorer handoff を起動できる
  - viewer は read-only のまま利用者の editor 作業へ渡せる
- `MRL-4`
  - launch method の候補と採用理由が明文化される
  - UI 全体構成の方針が compare viewer 前提で 1 本に定まる
  - 次の実装 line が UI 議論のやり直しなく開始できる

## 完了メモ

- `MRL-1` は multi-profile manifest、live snapshot、profile switch shell を実装した
- `MRL-2` は compare lane selection と cross-profile preview baseline を実装した
- `MRL-3` は `/api/dashboard/reveal` endpoint と contextmenu handoff を実装した
- `MRL-4` は `npm run dashboard` と compare viewer shell を launch baseline として固定した
