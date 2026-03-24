---
name: documentation-watchkeeper
description: 会話起点の文書影響を検知し、新しい判断、前提、範囲変更、統治更新、実装方針変更、重要な暫定規則を project 文書へ同期する。`docs/` に影響する code や plan を Codex が変更したとき、作業途中で user の方針が変わったとき、新しい運用規則が決まったとき、重要な方向性を漏れなく正しい文書へ反映すべきときに使う。
---

# Documentation Watchkeeper

## 適用境界

- 会話で決まった新しい事実や code 変更を、その turn のうちに文書へ反映すべきときに使う。
- archive 再編や旧 file の移設を主目的にするときの第一選択にはしない。
- 新しい project truth が増えていない状態での topology 正規化を主目的にするときの第一選択にはしない。

作業中の documentation drift を防ぐために使う。

## 中核規則
会話によって project truth が変わったら、その turn のうちに文書更新が必要かを確認する。

## 発動チェック
次のいずれかが起きたらこの skill を使う。
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
3. どれか 1 つを編集する前に、影響を受ける文書を洗い出す。
4. 最上位の source of truth を先に更新し、その後で下流の運用文書を更新する。
5. 作業中に route や process が変わった場合は、関連する進行中の process log も更新する。
6. 編集後は、次を明示的に確認する。
   - 記載漏れ
   - 矛盾
   - 古い参照
   - 上位文書に集約すべき重複記述

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
- まず `docs/index.md` を読み、現在の source-of-truth 配置を確認する。
