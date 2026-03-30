# Docker Recovery Patterns

## 障害分類

### host failure

- Docker daemon が起動していない
- Docker Desktop が不安定
- virtualization backend が壊れている
- host port が競合している

対応:

- host 側 service を再起動する
- host blocker であれば明示する
- project 側で復旧不能なら早めに切り分ける

### configuration failure

- `.env` 不足
- compose file mismatch
- mount path 不整合
- image build argument 不整合

対応:

- config を正本と照合する
- compose config を通す
- path と variable を固定する

### runtime failure

- container が crash する
- health check が失敗する
- migration が途中で止まる

対応:

- logs を確認する
- 失敗 service を再作成する
- 必要なら image を再 build する

### state failure

- volume 内 state が壊れている
- queue や DB state が不整合
- 前回失敗の残骸で通常起動できない

対応:

- reset 前に本当に state failure か確認する
- reset は最後の手段にする
- reset 後に同じ script 経路で再起動できることを確認する

## 収束確認

- 必要 service が running
- 必要 service が healthy
- 標準 script 経路で再起動できる
- 次の task でも同じ path を再利用できる
