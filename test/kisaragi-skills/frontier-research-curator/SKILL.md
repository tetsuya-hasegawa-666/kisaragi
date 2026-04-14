---
name: frontier-research-curator
description: `docs/reference/` 配下の frontier technology / frontier research note を収集、要約、比較、追記する。新しい先端技術の reference article を追加するとき、既存の research note を更新するとき、source material から現行 capability と将来 roadmap を抽出するとき、競合 approach を比較するとき、継続的な技術調査のために note 構造をそろえるときに使う。
---

# Frontier Research Curator

`docs/reference/` を、先端技術、research trend、product / platform の frontier note を蓄積する持続的な scouting library として保つために使う。

## Trigger Ownership

- この skill 自身は発火判断を持たない。
- `skill-invoker` と `skill-planner` が、frontier research の収集、比較、reference note 更新 task だと判断した時だけ呼ばれる。

## Workflow
1. `docs/reference/` 内の対象 file と、少なくとも 1 つの sibling note を読み、現地の書式に合わせる。
2. subject を分類する。
   - protocol / standard
   - framework / methodology
   - company / platform
   - research direction
3. `references/article-structure.md` の template を使って note を構成する。
4. source が許す限り、次の 5 点を記録する。
   - その subject が何か
   - 現在の frontier / 現在の展開水準
   - 次に何を目指しているか
   - product または system 設計への実務上の含意
   - source list / attribution note
5. speculative な note は、fact ではなく projection として明示する。
6. article は日本語で読みやすく保ち、evidence より hype が強くならないようにする。

## 執筆規則
- slogan より具体的な claim を優先する。
- 「現在できること」と「将来目標」を分けて書く。
- vendor claim、ecosystem の事実、inference を区別する。
- 技術比較を行うときは、同じ軸で比べる。
- source の確度が弱いときは、その旨を短く添える。
- 後続追記でも比較可能性を保てるよう、再利用構造を file 間で安定させる。

## File の扱い
- 既定の対象 directory は `docs/reference/` とする。
- user が明示的に rename を求めない限り、既存 filename は維持する。
- 新しい note を追加するときは、既存 file と同じ流儀で読める filename を選ぶ。
- note の方向性が大きく変わる場合のみ、関連する process 文書または reference 文書を必要範囲で更新する。

## 参照
- article の構成と section の意図は `references/article-structure.md` を読む。
