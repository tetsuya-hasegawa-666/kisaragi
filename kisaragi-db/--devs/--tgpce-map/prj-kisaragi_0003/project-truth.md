# project-truth

## 目的

`prj-kisaragi_0003` は、smartphone から Windows PC へ別系統で到達し、`Synceller` と `Slack` の接続異常時でも remote diagnosis と recovery を行って Codex 開発継続へ戻すための remote recovery project である。

## 完成判定

- iPhone または Android から Windows に private path で到達できる
- 主系統では `PowerShell` shell を直接開ける
- `doctor -> resume -> recheck -> summary` の contract が主系統と副系統で共有される
- `/codex status` の再疎通確認まで含めて closeout できる

## 利用入口

- 主入口は `Tailscale + OpenSSH Server + PowerShell + Termius`
- 副入口は `Tailscale + RustDesk`
- GUI launcher は補助入口として許容する

## UX 原則

- 主系統を優先し、副系統は補助導線にとどめる
- `doctor -> resume -> recheck -> summary` を operator 向けの共通 flow にする
- evidence は summary を `--testlogs`、raw を `--exsams` に分ける
- すべての復旧導線で同じ PowerShell script 群を使う

## 段階構造

### Reachability

- mobile から Windows へ private path で到達する

### Diagnosis

- `doctor` が `Slack`、`Docker`、`PostgreSQL`、`Synceller`、`app-server` の状態を返す

### Recovery

- `resume` が安全順序で復旧を実行する
- GUI fallback でも同じ recovery script を呼ぶ

### Closeout

- `recheck` と `summary` を返す
- `/codex status` 確認と capture 保存導線を持つ

## app 責務

### Mobile Client

- `Termius` を主系統の SSH client とする
- `RustDesk` を GUI fallback とする

### Windows Control

- `OpenSSH Server` を常駐させ、既定 shell は `PowerShell` とする
- recovery script は `scripts/` に集約する

### GUI Launcher

- desktop shortcut から read 系と action 系の recovery script を起動する

## artifact 契約

### command surface

- operator 向け command 名は `doctor`、`resume`、`recheck`、`summary` とする
- `recover` は経路全体の概念名としてのみ使う

### status model

- component status は `healthy`、`degraded`、`down`、`unknown` を使う
- overall status は `ready`、`needs_resume`、`needs_manual_intervention` を使う

### evidence layout

- summary は `kisaragi-db/--devs/--testlogs/prj-kisaragi_0003/` に置く
- raw 生成物は `kisaragi-db/--exsams/prj-kisaragi_0003/` に置く
- screenshot capture は `kisaragi-db/--exsams/prj-kisaragi_0003/captures/` に置く

## 外部連携境界

- network は `Tailscale` を前提とする
- shell は `OpenSSH Server` と `PowerShell` を前提とする
- GUI fallback は `RustDesk` を前提とする
- 対象 service は最低でも `Slack`、`Docker`、`PostgreSQL`、`Synceller`、`app-server` を監視する
- 将来拡張の vision は `remote-pwsh_add-vision.md` を参考情報として扱う
