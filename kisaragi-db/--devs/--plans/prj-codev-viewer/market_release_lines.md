# 2026-03-22-007 market release lines

## 目的

`2026-03-22-007` は、`iDevelop` を `prj-isensorium` 固定の consultation/archive viewer から、`codev-db` と `codev-view` を切り替える read-only comparison viewer へ再設計する plan set とする。

## planning rule

- `MRL-25` から `MRL-27` までは foundation line とする
- 起動方法と UI 全体構成は foundation line が閉じるまで仮決めしない
- `MRL-28` は foundation 後に entry command と UI 全般方針を定義する line とする

## market release lines

| ID | name | 提供価値 | status |
|---|---|---|---|
| MRL-25 | source profile foundation line | `codev-db` / `codev-view` を切り替える manifest と shell baseline を確立 | completed |
| MRL-26 | comparison workspace line | cross-profile document compare lane と read-only preview baseline を確立 | completed |
| MRL-27 | local handoff line | right click Explorer handoff と no-edit UX baseline を確立 | completed |
| MRL-28 | launch and UI direction line | 起動方法と UI 全体構成を foundation 後に定義 | completed |

## 完了条件

- `MRL-25`
  - source profile manifest contract が test で固定される
  - shell で active profile を切り替えられる
  - edit / draft / apply が UI から消える
- `MRL-26`
  - compare lane に文書を固定できる
  - 異なる profile の文書を同時に比較できる
  - compare empty / mismatch state を区別して示せる
- `MRL-27`
  - reveal target contract が roots 制約つきで固定される
  - right click から Explorer handoff を起動できる
  - viewer は read-only のまま利用者の editor 作業へ渡せる
- `MRL-28`
  - launch method の候補と採用理由が明文化される
  - UI 全体構成の方針が compare viewer 前提で 1 本に定まる
  - 次の実装 line が UI 議論のやり直しなく開始できる

## 完了メモ

- `MRL-25` は multi-profile manifest、live snapshot、profile switch shell を実装した
- `MRL-26` は compare lane selection と cross-profile preview baseline を実装した
- `MRL-27` は `/api/dashboard/reveal` endpoint と contextmenu handoff を実装した
- `MRL-28` は `npm run dashboard` と compare viewer shell を launch baseline として固定した
