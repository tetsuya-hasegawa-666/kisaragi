---
name: encoding-integrity-keeper
description: Markdown と text workflow を garbled text から守る。encoding が不安定な文書を読む前、mojibake が出たことがある文書を更新する前、PowerShell / git / Python の出力を信用する前、または UTF-8 へ正規化してから分析すべき場面で使う。
---

# Encoding Integrity Keeper

文書の encoding 信頼性が重要なときは、読む前や更新前にこの skill を使う。

## コアルール

可読性を確認する前に文書を分析しない。
文書が garbled なら、先に正規化または復旧する。
mojibake を前提に推論しない。
文書が garbled なら、復旧は optional cleanup ではなく必須作業として扱う。

## 既知の危険点

- PowerShell terminal output
- `git` diff や file 表示
- `apply_patch` 後の再読
- Python script の stdout / stderr
- Markdown の保存経路

## 使う場面

- mixed encoding の可能性がある Markdown を読む前
- mojibake 履歴のある古い文書を更新する前
- UTF-8 が必要だが file 由来が不明なとき
- terminal や editor ですでに文字化けが見えているとき
- Windows PowerShell で文書中心の作業を行う前

## 手順

1. runtime 状態が不明なら、文書中心作業の前に `scripts/check_text_runtime_utf8.py` を実行する。
2. 詳しく読む前に `scripts/check_markdown_encoding.py <path>` を実行する。
3. file が UTF-8 で問題なければ通常どおり読む。
4. 復旧可能だが UTF-8 でなければ `scripts/normalize_markdown_utf8.py <path>` を実行する。
5. 正規化後に 1 回だけ再確認する。
6. まだ suspicious なら、正しい upstream source、clean reference file、または既知の良い git version から復旧する。
7. 復旧内容を UTF-8 で保存し、1 回だけ再確認する。
8. 原因を簡潔に記録し、再発防止の最小変更を入れる。
9. file edit 後は壊れた出力を何度も読み直さず、触った Markdown を 1 回だけ再確認する。

## 運用ルール

- 繰り返し読み直すより、安い preflight check を 1 回入れる
- mojibake は通常の文書内容ではなく input integrity 問題として扱う
- 復旧で file を書き換えた場合は、必要に応じて work log や current-state に触れる
- local byte から復旧不能なら clean source から戻して UTF-8 に正規化する
- runtime UTF-8 check が失敗したら terminal output を信用する前に runtime 側を直す
- 復旧は、再び garble する経路を特定して弱めるまで完了ではない

## script

- `scripts/check_text_runtime_utf8.py`
  PowerShell、Python、git の出力が UTF-8-safe か確認する。
- `scripts/check_markdown_encoding.py`
  可能性の高い encoding を検出し、mojibake を疑う。
- `scripts/normalize_markdown_utf8.py`
  復旧可能な text file を UTF-8 と正規化 line ending で書き直す。
