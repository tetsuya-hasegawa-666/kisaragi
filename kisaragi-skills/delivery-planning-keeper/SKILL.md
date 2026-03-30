---
name: delivery-planning-keeper
description: BDD、TDD、release gate、handover を 1 本の流れとして扱う。behavior 設計、test task 化、gate 判定、session handover を同じ文脈で扱うときに使う。
---

# Delivery Planning Keeper

delivery planning を、`BDD -> TDD -> release gate -> handover` の連続した作業として扱うための skill とする。

## 吸収した観点

- `bdd-story-builder` の scenario から terminal behavior を作る観点
- `tdd-testflow-manager` の behavior から task / criterion を作る観点
- `release-line-gatekeeper` の gate readiness を評価する観点
- `session-handover-writer` の継続用 handover を短く残す観点

## Workflow

1. 具体的な scenario または現在の gate 対象を 1 件定義する。
2. `experience -> touchpoints -> value -> function elements -> technology elements` の順に整理する。
3. terminal behavior を抽出し、acceptance criteria を定義する。
4. behavior ごとに TDD task と測定可能 criterion を作る。
5. release gate の pass / blocked と最小 next action を判定する。
6. session をまたぐなら、decision、未解決、次 action を handover として残す。

## 必須出力

- story summary
- acceptance criteria table
- TDD task table
- RL / MRL gate status
- 必要時のみ handover note

## 参照

- `references/bdd_structure_template.md`
- `references/tdd_mapping_template.md`
- `scripts/make_mapping.py`
