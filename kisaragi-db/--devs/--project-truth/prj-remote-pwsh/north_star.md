# North Star

## 目的

remote-pwsh の目的は、smartphone から Windows PC へ別系統で到達し、`Synceller` と `Slack` の接続異常時でも開発継続に戻せる生命線を提供することである。

## 提供価値

1. iPhone と Android のどちらからでも Windows の shell に入れる。
2. `Slack`、`Docker`、`PostgreSQL`、`Synceller` のいずれかが不安定でも、別系統で状態確認と復旧を行える。
3. 主系統の shell 復旧と、副系統の GUI fallback を分けて運用できる。
4. 復旧結果と次の判断を evidence として残せる。

## 非交渉条件

- 主系統は smartphone からの shell 操作で完結できる。
- 副系統は GUI fallback とし、主系統の代替ではなく補助とする。
- `remote-pwsh` 自体は `Slack` や `Synceller` の可用性に依存しない。
- iPhone と Android の両方で使える構成にする。
- 復旧操作は、要約を `kisaragi-db/--devs/--testlogs/prj-remote-pwsh/` に、raw 生成物を `kisaragi-db/--exsams/prj-remote-pwsh/` に残せる形にする。

## 成功条件

- smartphone から Windows の `PowerShell` に到達できる。
- 遠隔から `Synceller` の状態診断と復旧 command を実行できる。
- 主系統が使えない場合に GUI fallback へ切り替えられる。
- operator が外出先でも Codex 開発継続に戻せる。
