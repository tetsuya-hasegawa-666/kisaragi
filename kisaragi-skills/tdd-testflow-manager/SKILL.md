---
name: tdd-testflow-manager
description: BDD の terminal behavior から TDD task と測定可能な criteria を導く。behavior-level validation のために Codex の実装 / test 作業を計画または追跡するときに使う。
---

# TDD Testflow Manager

behavior leaf を実行可能な TDD task へ変換するために使う。

## Workflow
1. BDD の terminal behavior を読む。
2. behavior ごと、または密接に結び付いた 2 件ごとに TDD task を作る。
3. 各 task の測定可能 criteria を定義する。
4. status と blocker を追跡する。
5. 簡潔な execution plan を出す。

## 必須 table 列
- task_id
- behavior_id
- test_target
- criterion
- status
- evidence

## 規則
- 1 task 1 responsibility を保つ。
