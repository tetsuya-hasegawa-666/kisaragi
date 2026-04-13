# dependency scan scope

## 目的

- `runtime-structure-dependency-mapper` が何を棚卸し対象に含めるかを固定する。

## 必須対象

- `import/呼び出し関係`
- `path read/write`
- `artifact producer/consumer`
- `directory structure`

## 補助対象

- manifest key
- helper 所有
- input / output contract 名

## 対象外

- 純粋な文言修正だけで、runtime や handoff に影響しないもの
- UI 文言変更だけで path / artifact を持たないもの
