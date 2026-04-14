---
name: documentation-watchkeeper
description: 会話起点の文書影響を検知し、新しい判断、前提、範囲変更、統治更新、実装方針変更、重要な暫定規則を project 文書へ同期する。docs drift だけでなく、文書 topology、version 整合、encoding 健全性も同じ turn で扱う。
---

# Documentation Watchkeeper

## Trigger Ownership

- この skill 自身は発火判断を持たない。
- `skill-invoker` と `skill-planner` が、文書同期または docs drift close が必要と判断した時だけ呼ばれる。

## 吸収した観点

- `documentation-watchkeeper` の docs drift 検知
- `document-topology-keeper` の authoritative / pointer 整理
- `doc-governor` の version / archive 整合
- `encoding-integrity-keeper` の UTF-8 preflight と mojibake 防止

作業中の documentation drift を防ぐために使う。

## 中核規則
会話によって project truth が変わったら、その turn のうちに文書更新が必要かを確認する。
可読性が壊れている文書を、そのまま真実として扱わない。

## 呼び出し対象となる典型条件
次のいずれかが起きた時に、通常は distributor / planner からこの skill が呼ばれる。
- 新しい policy、rule、approval gate が決まった
- 実装範囲や進め方が変わった
- 新しい branch、release、deployment rule が導入された
- 新しい report、process file、evidence file が workflow に入った
- 文書で支えていた assumption が、より良い decision に置き換わった
- code 変更により既存文書が不完全または誤解を招く状態になった

## Workflow
1. 会話または code 変更から、新しい project truth を抽出する。
2. その truth を分類する。
   - concept / principle
   - branch / release governance
   - test または execution process
   - reference knowledge
   - handover または operational log
3. 編集前に、対象文書の encoding が信頼できるかを確認する。必要なら `scripts/` で UTF-8 正規化する。
4. どれか 1 つを編集する前に、影響を受ける文書と authoritative / pointer の役割を洗い出す。
5. 最上位の source of truth を先に更新し、その後で下流の運用文書を更新する。
6. archive や旧版を持つ場合は current / archive の整合を確認する。
7. 作業中に route や process が変わった場合は、関連する進行中の process log も更新する。
8. 編集後は、次を明示的に確認する。
   - 記載漏れ
   - 矛盾
   - 古い参照
   - 上位文書に集約すべき重複記述
   - UTF-8 可読性

## 優先順
1. `docs/artifact/north_star.md` and `docs/artifact/problem_and_assumptions.md` for principles and assumptions
2. `docs/artifact/architecture.md` and `docs/artifact/decision_log.md` for design and important decisions
3. `docs/process/*` for collaboration rules, decision policy, and documentation policy
4. `docs/artifact/current_state.md` for ongoing work, confirmations, and next actions
5. `docs/observability/*` and `docs/metrics/*` for short-term logs and quality indicators
6. `docs/reference/*` for frontier knowledge articles

## 編集規則
- source-of-truth 文書も変わるなら、log 追記だけで済ませない。
- 新しい運用規則を chat にだけ残さない。
- 複数 file にまたがる記述なら、理由は上位文書に、具体 rule は下位文書に置く。
- 一時的 assumption が決定済み rule になったら、rule として書き直す。
- 文書更新が不要だった場合も、確認したうえで不要と明示する。

## 参照

- `references/`
- `scripts/check_text_runtime_utf8.py`
- `scripts/check_markdown_encoding.py`
- `scripts/normalize_markdown_utf8.py`
