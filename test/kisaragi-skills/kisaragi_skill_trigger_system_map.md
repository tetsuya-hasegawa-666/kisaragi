# kisaragi skill trigger system map

## 目的

- `prompt -> receipt-manager -> skill-invoker -> skill-planner -> execution -> response-manager` の主線を図で固定する。
- ownership と handoff の境界を図で読めるようにする。

## 全体構造

```mermaid
flowchart TD
    U["prompt"] --> R["receipt-manager / 解釈と要求整理"]
    R --> I["skill-invoker / skill 集合確定"]
    I -->|selected skills| P["skill-planner / 発火と順序管理"]
    P --> E["execution skills / manager と specialist"]
    E --> M["response-manager / 応答整形"]
```

## ownership map

```mermaid
flowchart LR
    R["receipt-manager"] --> A1["prompt review"]
    R --> A2["明示要求抽出"]
    R --> A3["暗黙要求抽出"]
    R --> A4["制約整理"]

    I["skill-invoker"] --> B1["skill 要否判断"]
    I --> B2["read_set_minimum 決定"]
    I --> B3["defer / block 判定"]
    I --> B4["skill 集合確定"]

    P["skill-planner"] --> C1["実行順管理"]
    P --> C2["phase 管理"]
    P --> C3["handoff 固定"]
    P --> C4["close 条件固定"]

    M["response-manager"] --> D1["粒度調整"]
    M --> D2["形式整形"]
    M --> D3["残件提示"]
```

## 現行 skill の位置づけ

```mermaid
flowchart TD
    I["skill-invoker"] --> H1["rule-snapshot-reader"]
    I --> H2["authoritative-doc-scope-resolver"]
    I --> H3["rule-diff-clarifier"]

    P["skill-planner"] --> T1["task-intent-normalizer"]
    P --> T2["task-scope-splitter"]
    P --> T3["close-condition-definer"]
    P --> T4["phase-task-orchestrator"]

    P --> S1["documentation-watchkeeper"]
    P --> S2["design-first-script-builder"]
    P --> S3["reference-rewire-operator"]
    P --> S4["delivery-planning-keeper"]
    P --> S5["runtime-structure-dependency-mapper"]
    P --> S6["external-compute-output-keeper"]
    P --> S7["runtime-operator"]
    P --> S8["test-and-evidence-recorder"]
```

## 旧構成との対応

| 旧 | 新 |
| --- | --- |
| 旧単一入口の prompt review 部分 | `receipt-manager` |
| 旧単一入口の最終選定部分 | `skill-invoker` |
| `skill-planner` | `skill-planner` のまま維持 |
| 応答整形の暗黙処理 | `response-manager` |

## 標準 handoff 順

```mermaid
sequenceDiagram
    participant U as prompt
    participant R as receipt-manager
    participant I as skill-invoker
    participant P as skill-planner
    participant E as execution skills
    participant M as response-manager

    U->>R: prompt
    R->>I: 解釈済み要求
    I->>P: selected / deferred / blocked / read_set
    P->>E: execution plan
    E-->>M: results
    M-->>U: formatted response
```
