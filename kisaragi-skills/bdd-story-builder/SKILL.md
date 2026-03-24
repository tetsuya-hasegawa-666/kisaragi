---
name: bdd-story-builder
description: 現場の具体的な use-case から BDD story を構築し、磨き込む。scenario を experience-touchpoint-value-function-technology 構造と behavior-level 定義へ変換するときに使う。
---

# BDD Story Builder

現実の scenario を test 可能な behavior model へ変換するために使う。

## Workflow
1. 具体的な scenario を 1 件定義する。
2. `experience -> touchpoints -> value -> function elements -> technology elements` の順に展開する。
3. sequence flow を作る。
4. behavior leaf（terminal behavior）を定義する。
5. leaf を acceptance criteria へ対応付ける。

## 出力形式
- story summary
- sequence（Mermaid）
- behavior leaf 一覧
- acceptance criteria table
