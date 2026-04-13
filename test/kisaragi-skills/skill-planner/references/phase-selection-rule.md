# phase selection rule

## 目的

- `skill-planner` が `phase-task-orchestrator` を呼ぶかどうかを判断するための基準とする。

## 分類

### single-step

- 単一責務
- specialist 1 本で閉じる
- docs / test / evidence が局所で閉じる

### multi-step

- specialist 複数本が必要
- ただし full phase を書かなくても順序管理で足りる

### multi-phase

- 複数 task
- code / docs / test / evidence がまたがる
- 中断再開や確認待ちが入りやすい
- `Phase 1` と `Phase 4` を明示した方が安全

## multi-phase に倒す目安

- `script` と文書を同時更新する
- 参照切替や path 変更を含む
- external compute を含む
- gate / evidence まで close 条件に入る
