# phase task template

## 基本形

```text
Task Header
- Goal:
- Authoritative:
- Working files:
- Do not treat as truth:
- Close condition:

Phase 1: authoritative context 確定
- 読む文書:
- 決めること:
- 完了条件:

Phase 2: 設計確定と参照面棚卸し
- old -> new 対応:
- 影響対象:
- 非対象:
- 完了条件:

Phase 3: code / docs 編集
- 編集対象:
- 同期対象:
- 完了条件:

Phase 4: probe / test / link check
- 実行:
- 期待結果:
- 完了条件:

Phase 5: evidence / closeout
- evidence path:
- remaining work:
- 完了条件:
```

## 軽量形

```text
Goal:
Authoritative:
Close condition:

P1 context
P2 design
P3 edit
P4 verify
P5 closeout
```

## 省略ルール

- 単純な局所修正なら `Phase 2` と `Phase 3` をまとめてよい。
- 文書だけの更新でも `Phase 1` と `Phase 4` は残す。
- test が物理的に無い時も `Phase 4` を消さず、未実施理由を書く。
