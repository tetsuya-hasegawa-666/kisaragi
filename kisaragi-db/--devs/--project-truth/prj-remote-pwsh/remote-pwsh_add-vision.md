# remote-pwsh Add Vision

## 目的

この文書は、現在の `remote-pwsh` を `Slack` 連携の復旧導線にとどめず、どこからでも Codex と作業継続できる remote work substrate として拡張する UX 提案をまとめる。

## 前提

- 主目的は `Synceller` と `Slack` の連携を切らさないこと
- ただし UX は recovery 専用の緊急装置で終わらせず、平常時にも価値がある方が採用されやすい
- fail-safe と fool-proof を前提にする
- ただし操作性を落とさない

## UX 原則

### 1. 平常時にも使いたくなる

- 緊急時専用ではなく、普段から `doctor`、log 確認、軽作業、Codex 継続に使える
- operator が日常的に触るほど、障害時の迷いが減る

### 2. 多重 session を価値に変える

- 1 本は recovery 操作用
- 1 本は監視用
- 必要なら 1 本は Codex CLI や補助作業用
- ただし危険操作だけは lock で保護する

### 3. fail-safe を既定にする

- 読み取り系は何本でも開ける
- 書き込み系は明示的に制限する
- `resume` の二重実行は script 側で止める
- 障害時は「壊さないまま次の安全な判断を返す」ことを優先する

### 4. fool-proof を UI と wording で実現する

- `Hostname`、password、`Use Telnet` のような迷いやすい点は runbook に具体例を書く
- operator が端末、app、入力欄を迷わない粒度まで分解する
- shell / GUI / Slack の役割を分けて説明する

## 目指す体験像

operator は外出先でも `smartphone` から Windows に入り、必要なら複数 session を開きながら、状態確認、復旧、Codex 継続、チーム連携を止めずに進められる。

## 提案 UX ストーリー

### Story 1: 30 秒で Slack 復旧に戻る

#### 構想

`Slack` の `/codex` が止まったとき、operator は smartphone から `Termius` を開き、最短手順で `doctor -> resume -> doctor -> /codex status` を終えたい。

#### 設計

- 主系統は `remote-pwsh-primary` 1 接続で完結する
- `doctor` は component ごとに `healthy / degraded / down / unknown` を返す
- `summary` は次の 1 行判断を返す
- `resume` は lock 付きで二重実行を拒否する

#### 検証

- `Termius` 接続から `doctor` まで 30 秒以内
- `resume` 後に `/codex status` 応答が返る
- evidence path が自動で出る

#### 価値

- ソフトウェアエンジニアでなくても「まずこの 4 手順」と覚えれば復旧できる

### Story 2: 監視用 session と操作用 session を分ける

#### 構想

operator は recovery 中に 2 本目の shell を開き、1 本目で `resume`、2 本目で log や process を見る。

#### 設計

- `session A`: `doctor` / `resume` / `recheck`
- `session B`: `Get-Content -Wait`, process 確認, evidence 確認
- `resume` 実行中は lock file を持つ
- `session B` から `resume` を叩くと「別 session が実行中」と返す

#### 検証

- 2 本の `pwsh` が同時に開いても読み取り系は競合しない
- `resume` は 1 本しか走らない

#### 価値

- 状況確認しながら安全に操作できる
- 緊急時の不安が減る

### Story 3: smartphone から Codex CLI を補助的に使う

#### 構想

Slack が不安定でも、operator は smartphone の shell から Windows 上の Codex CLI や関連 command を起動し、最低限の作業継続をしたい。

#### 設計

- recovery 導線とは別 session で補助 shell を開く
- Codex CLI 系は read / inspect 中心に使う
- recovery session と同じ shell に重ねず、役割を分ける
- 長時間操作は GUI fallback へ逃がせる

#### 検証

- `doctor` と別 session で補助 command を起動しても recovery を阻害しない
- operator が `Slack` 不通時にも最低限の開発継続に戻れる

#### 価値

- 「復旧して終わり」ではなく「その場で仕事を継続できる」
- 個別作業にもチーム作業にも使える

### Story 4: GUI fallback でも同じ mental model で使う

#### 構想

SSH 認証や shell が詰まったとき、operator は `RustDesk` に切り替えるが、覚え直しはしたくない。

#### 設計

- GUI fallback でも実行する script 名は同じ
- `doctor`、`resume`、`recheck`、`summary` を GUI の `PowerShell` から呼ぶ
- decision matrix に「いつ GUI に移るか」を固定する

#### 検証

- smartphone の `RustDesk` から Windows に入り、同じ command が打てる
- operator が shell と GUI で別の手順を覚えなくて済む

#### 価値

- 非エンジニアでも「入口は違うが command は同じ」と理解しやすい

### Story 5: long-idle 後でも迷わず戻れる

#### 構想

夜間放置や移動中の切断後、operator は朝に smartphone から状態を見て、必要最小限だけ復旧し、すぐに通常作業へ戻りたい。

#### 設計

- `doctor` は long-idle の典型異常を summary に出す
- `resume` は `Docker`、`PostgreSQL`、`Synceller`、`app-server` を安全順序で扱う
- `/codex status` の capture を closeout 条件にする

#### 検証

- long-idle 後でも `doctor -> resume -> /codex status` で復帰できる
- operator が次に何をするか迷わない

#### 価値

- 「朝の復旧」が定型化される
- remote-pwsh が日常運用にも価値を持つ

### Story 6: 非エンジニアでも使える recovery assistant

#### 構想

開発者本人でなくても、決められた手順を辿れば最低限の復旧確認ができるようにする。

#### 設計

- runbook は端末名、app 名、入力欄名まで書く
- summary は技術 detail と operator 向け判断を分ける
- `ready / needs_resume / needs_manual_intervention` の 3 値で返す
- 危険操作は hidden にして、通常 operator は触れない

#### 検証

- 専門用語を深く知らない user でも `doctor` と `summary` を解釈できる
- 誤操作なしで evidence まで残せる

#### 価値

- remote-pwsh が「エンジニアだけの道具」にならない
- チーム支援にも使える

## かたい設計

### 排他制御

- `resume` は global lock を取る
- stale lock には timeout と operator override を持つ
- `doctor` と `recheck` は lock 不要

### role 分離

- read role: `doctor`, log, status
- action role: `resume`, host config
- assist role: Codex CLI, note, report

### safety defaults

- `WhatIf` を既定にできる command は既定 dry-run にする
- destructive 操作は別 command に分離する
- `summary` が `ready` でない限り closeout しない

### evidence

- session 単位で evidence path を発行する
- `/codex status` capture を evidence の一部にする
- GUI fallback の screenshot も evidence に含められるようにする

## 提案する将来の command UX

### lightweight

- `remote-pwsh doctor`
- `remote-pwsh resume`
- `remote-pwsh status`
- `remote-pwsh follow`

### guided

- `remote-pwsh doctor --guided`
  - 次の 1 手を返す
- `remote-pwsh recover --guided`
  - `doctor -> resume -> recheck -> summary` を 1 つで流す
- `remote-pwsh handoff`
  - team 向けの共有 summary を作る

## 追加で文書化すべきもの

1. `resume` lock 設計
2. `/codex status` capture の保存手順
3. `RustDesk` 初回設定マニュアル
4. multi-session 運用ルール
5. Codex CLI を補助的に使うときの安全範囲

## 結論

remote-pwsh は単なる障害復旧手順ではなく、`Slack` を主導線としながら、shell、GUI、Codex、team coordination を補完する remote continuity UX に育てられる。

そのためには、操作性を維持しつつ、`resume` の排他制御、guided summary、multi-session の役割分離を実装し、平常時にも触りたくなる道具にするのがよい。
