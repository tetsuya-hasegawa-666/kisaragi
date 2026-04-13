# kisaragi skill trigger system map

## 目的

- `prompt -> skill-distributor -> skill-planner -> specialist` の主線を図で固定する。
- `rule / authority` と `task structuring` は独立した `系` ではなく、distributor / planner が必要時に参照する内部補助 specialist として扱う。
- trigger ownership、発火と実行順管理 owner、specialist の役割境界を図で読めるようにする。

## 全体構造

```mermaid
flowchart TD
    U["prompt"] -->|開発 prompt| D["skill-distributor / 入口と最終選定"]
    D -->|skill 不要| NS["no-skill path"]
    D -->|選定済み skill 集合を handoff| P["skill-planner / 発火と実行順管理"]

    D -.->|必要時に内部参照| RA["rule / authority 補助 specialist"]
    P -.->|必要時に内部参照| TS["task structuring 補助 specialist"]

    P -->|発火: code と文書同期| SD["script / docs 同期系"]
    P -->|発火: 依存棚卸し| RT["runtime / structure 依存系"]
    P -->|発火: 設計 or 参照切替| DR["設計 / 参照切替系"]
    P -->|発火: BDD TDD gate| PG["planning / gate 系"]
    P -->|発火: Colab remote| EC["external compute 系"]
    P -->|発火: 調査 runtime| RR["research / runtime 系"]

    SD -->|記録反映| CE["closeout / evidence 系"]
    RT -->|probe 結果| CE
    DR -->|変更根拠| CE
    PG -->|gate 状態| CE
    EC -->|output evidence| CE
    RR -->|調査結果| CE
```

## ownership map

```mermaid
flowchart LR
    D["skill-distributor"] --> O1["prompt review"]
    D --> O2["skill 要否判断"]
    D --> O3["mark 解釈"]
    D --> O4["最終 skill 集合の確定"]
    D --> O14["内部補助 specialist 参照"]

    P["skill-planner"] --> O5["選定済み skill の発火"]
    P --> O6["実行順管理"]
    P --> O7["phase 配置"]
    P --> O8["handoff packet 固定"]
    P --> O13["close 条件固定"]
    P --> O15["内部補助 specialist 参照"]

    S["specialist skills"] --> O9["処理責務"]
    S --> O10["受入前提"]
    S --> O11["完了条件"]
    S --> O12["失敗条件"]
```

## distributor / planner 配下の推奨 tree

```mermaid
flowchart TD
    D["skill-distributor"]
    D -->|内部補助 specialist| RA["rule / authority 補助 specialist"]
    D -->|選定済み集合を渡す| P["skill-planner"]

    RA -->|最新 rule| RA1["rule-snapshot-reader"]
    RA -->|管理文書範囲| RA2["authoritative-doc-scope-resolver"]
    RA -->|rule 差分| RA3["rule-diff-clarifier"]

    P -->|内部補助 specialist| TS["task structuring 補助 specialist"]
    P -->|同期系を発火| SD["script / docs 同期系"]
    P -->|依存系を発火| RT["runtime / structure 依存系"]
    P -->|設計系を発火| DR["設計 / 参照切替系"]
    P -->|planning 系を発火| PG["planning / gate 系"]
    P -->|external 系を発火| EC["external compute 系"]
    P -->|research 系を発火| RR["research / runtime 系"]
    P -->|closeout 系を発火| CE["closeout / evidence 系"]

    TS -->|intent 正規化| TS1["task-intent-normalizer"]
    TS -->|task 分割| TS2["task-scope-splitter"]
    TS -->|close 条件| TS3["close-condition-definer"]

    SD -->|code docs test 記録| SD1["script-doc-sync-enforcer"]
    SD -->|docs drift| SD2["documentation-watchkeeper"]
    SD -->|更新先特定| SD3["doc-target-resolver"]
    SD -->|evidence 記録| SD4["test-and-evidence-recorder"]

    RT -->|依存棚卸し| RT1["runtime-structure-dependency-mapper"]
    RT -->|handoff 整理| RT2["artifact-handoff-mapper"]
    RT -->|path 契約| RT3["path-contract-scanner"]

    DR -->|設計固定| DR1["design-first-script-builder"]
    DR -->|参照切替| DR2["reference-rewire-operator"]
    DR -->|phase 化| DR3["phase-task-orchestrator"]

    PG -->|BDD TDD gate| PG1["delivery-planning-keeper"]

    EC -->|output 保全| EC1["external-compute-output-keeper"]
    EC -->|Drive input| EC2["drive-input-bootstrap-checker"]
    EC -->|bootstrap 範囲| EC3["runtime-bootstrap-scope-resolver"]

    RR -->|外部調査| RR1["frontier-research-curator"]
    RR -->|runtime 安定化| RR2["runtime-operator"]

    CE -->|記録先確定| CE1["evidence-destination-resolver"]
    CE -->|log 昇格抽出| CE2["log-promotable-facts-extractor"]
```

## 主な specialist 系の役割

```mermaid
flowchart TB
    SD["script / docs 同期系 / code と正本文書と記録の同期"] -->|close 情報| C["closeout"]
    RT["runtime / structure 依存系 / import / path / artifact / directory 棚卸し"] -->|close 情報| C
    DR["設計 / 参照切替系 / 設計固定 / path / contract 切替"] -->|close 情報| C
    PG["planning / gate 系 / BDD / TDD / gate / handover"] -->|close 情報| C
    EC["external compute 系 / Drive mount / input 解決 / output 保全"] -->|close 情報| C
    RR["research / runtime 系 / 外部調査 / branch / Docker / FastAPI"] -->|close 情報| C
```

## 内部補助 specialist の位置づけ

```mermaid
flowchart TD
    D["skill-distributor"] -->|必要時に使う| R1["rule-snapshot-reader"]
    D -->|必要時に使う| R2["authoritative-doc-scope-resolver"]
    D -->|必要時に使う| R3["rule-diff-clarifier"]

    P["skill-planner"] -->|必要時に使う| T1["task-intent-normalizer"]
    P -->|必要時に使う| T2["task-scope-splitter"]
    P -->|必要時に使う| T3["close-condition-definer"]

    R1 -->|補助| D
    R2 -->|補助| D
    R3 -->|補助| D
    T1 -->|補助| P
    T2 -->|補助| P
    T3 -->|補助| P
```

## モデル比較

```mermaid
flowchart LR
    A["集中型 / distributor が全判断"] -->|評価| A1["利点: 単純"]
    A -->|評価| A2["欠点: distributor が重い"]

    B["半集中型 / distributor + 補助 controller"] -->|評価| B1["利点: 再利用しやすい"]
    B -->|評価| B2["欠点: 境界が曖昧だと drift"]

    C["分散型 / 各系が自分で判断"] -->|評価| C1["利点: 自律度が高い"]
    C -->|評価| C2["欠点: kisaragi では drift しやすい"]
```

## 現時点の推奨

```mermaid
flowchart TD
    R["推奨モデル"] -->|現時点| A["集中型"]
    A -->|最上位判断と最終選定| A1["skill-distributor"]
    A -->|発火と実行順管理| A2["skill-planner"]
    A1 -->|必要時に内部参照| A3["rule / authority 補助 specialist"]
    A2 -->|必要時に内部参照| A4["task structuring 補助 specialist"]
    A2 -->|選定済み skill を発火| A5["下位 specialist"]
```

## 発火順の標準

```mermaid
sequenceDiagram
    participant U as prompt
    participant D as skill-distributor
    participant RA as rule/authority補助
    participant P as skill-planner
    participant TS as task structuring補助
    participant S as specialist系
    participant C as closeout/evidence系

    U->>D: prompt
    D->>D: review / 要否判断 / mark 解釈 / 最終選定
    opt rule 確定が要る時
        D->>RA: 必要時に参照
        RA-->>D: rule 補助情報
    end
    alt skill 不要
        D-->>U: no-skill path
    else skill 必要
        D->>P: 選定済み skill 集合を handoff
        opt task 整理が要る時
            P->>TS: 必要時に参照
            TS-->>P: task 補助情報
        end
        P->>S: 選定済み skill を発火
        S->>C: closeout が必要な時
    end
```

## 定義済み child skill

```mermaid
flowchart LR
    A["rule-snapshot-reader"] -->|distributor child| E["定義済み child skill"]
    B["authoritative-doc-scope-resolver"] -->|distributor child| E
    C["rule-diff-clarifier"] -->|distributor child| E
    D["task-intent-normalizer"] -->|planner child| E
    F["task-scope-splitter"] -->|planner child| E
    G["close-condition-definer"] -->|planner child| E
```
