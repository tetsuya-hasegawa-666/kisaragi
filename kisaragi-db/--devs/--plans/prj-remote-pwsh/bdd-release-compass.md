# BDD リリースコンパス

この文書は、active plan set における user value と release line の対応をまとめる。

## ノーススター

operator が smartphone から Windows PC を遠隔監視操作し、`synceller` と `Slack` の接続異常を復旧して Codex 開発継続に戻れるようにする。

## 提供方針

- shared recovery contract を先に固める
- 生命線として必要な主系統を先に集中して作る
- 副系統は shared contract 完了後に並行化してよい

## コアストーリー

1. operator は iPhone または Android から Windows PC に private path で到達できる
2. operator は smartphone から Windows `PowerShell` を使える
3. operator は `synceller` と周辺依存の状態を remote で診断できる
4. operator は remote から復旧 command を実行できる
5. operator は主系統が使えない場合に副系統へ切り替えられる
6. operator は復旧後に Slack から Codex 開発継続へ戻れる
7. operator は GUI fallback で launcher icon から recovery action を起動できる
8. operator は複数 session を安全に使い分けられる
9. operator は guided command と capture 保存導線で closeout を迷わない

## 対応ルール

- gate closeout は `Recorded_Release_Line.md` に記録する
- TDD 計画は `tdd-test-matrix.md` に記録する
- hands-on UX は `../../hands-on_results/2026-03-20-001/` に記録する

## MRL 対応表

### MRL-1 復旧契約基準

- user stories: `1`, `3`
- current gate: `pass`

#### mRL-1.1 環境インベントリ

- iPhone、Android、Windows の必須 app と software を確定する
- gate: `pass`

#### mRL-1.2 共通復旧契約

- `doctor -> recover -> recheck -> summary` の contract を定義する
- gate: `pass`

#### mRL-1.3 BDD / TDD 基準

- 目標 UX、behavior leaves、TDD task を plan に落とす
- gate: `pass`

### MRL-2 主系統モバイル shell 経路

- user stories: `1`, `2`, `4`
- current gate: `pass`

#### mRL-2.1 Tailscale 到達性

- mobile から Windows への private path を設計する
- gate: `pass`

#### mRL-2.2 OpenSSH PowerShell 入口

- Windows `PowerShell` を remote shell の既定入口にする
- gate: `pass`

#### mRL-2.3 モバイル接続 profile

- iPhone と Android で使う接続 profile を runbook 化する
- gate: `pass`

### MRL-3 復旧コマンド経路

- user stories: `3`, `4`, `6`
- current gate: `pass`

#### mRL-3.1 診断ラッパー

- `synceller` 用の診断 command と summary 出力を固定する
- gate: `pass`

#### mRL-3.2 復旧ラッパー

- `doctor -> recover -> recheck` の安全順序 script を作る
- gate: `pass`

#### mRL-3.3 証跡出力

- `--process/--testlogs/prj-remote-pwsh/` に結果を残す
- gate: `pass`

### MRL-4 副系統 GUI fallback

- user stories: `5`
- current gate: `pass`

#### mRL-4.1 RustDesk 到達性

- mobile から Windows GUI に入る経路を定義する
- gate: `pass`

#### mRL-4.2 共通 script 呼び出し

- GUI fallback でも主系統と同じ recovery script を使う
- gate: `pass`

### MRL-5 リモート復旧運用

- user stories: `4`, `5`, `6`
- current gate: `pass`

#### mRL-5.1 判断マトリクス

- 主系統継続、副系統移行、手動介入の分岐条件を runbook 化する
- gate: `pass`

#### mRL-5.2 長時間待機後の復旧 UX

- 長時間放置後の `synceller` 復旧を smartphone から確認する
- gate: `pass`

### MRL-6 GUI launcher UX

- user stories: `5`, `7`
- current gate: `pass`

#### mRL-6.1 launcher 仕様

- read 系と action 系の GUI launcher を定義する
- gate: `pass`

#### mRL-6.2 launcher script 群

- launcher から同じ recovery script を起動する
- gate: `pass`

#### mRL-6.3 デスクトップショートカット配置

- desktop 配置の手順を runbook 化する
- gate: `pass`

### MRL-7 安全な guided 操作

- user stories: `8`, `9`
- current gate: `pass`

#### mRL-7.1 resume lock

- `resume` の二重実行を lock で防ぐ
- gate: `pass`

#### mRL-7.2 guided recovery UX

- guided command で `doctor -> resume -> recheck -> summary` を返す
- gate: `pass`

#### mRL-7.3 capture と multi-session 方針

- capture 保存導線と multi-session ルールを固定する
- gate: `pass`
