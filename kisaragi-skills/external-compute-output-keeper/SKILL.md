---
name: external-compute-output-keeper
description: `Colab`、remote notebook、remote GPU job などの外部コンピューティング task で、確定出力を永続 visible storage へ先保存し、cleanup で消してよい不可視中間生成物だけを分離するときに使う。
---

# External Compute Output Keeper

外部コンピューティング task で、final output を download 成否に依存させず残すための skill とする。

## 適用条件

- `Colab`
- remote notebook
- remote GPU job
- runtime 切断や download timeout が起こりうる長時間処理
- Drive などの visible storage と local tmp / zip を併用する task

## Workflow

1. final output と、その再解釈に最低限必要な manifest / summary / transform 情報を先に列挙する。
2. 永続 visible storage 側の canonical tree を runbook の早い block で先に作る。
3. final merge / final export が終わったら、download や local zip より先に final output と付随情報を canonical tree へ保存する。
4. `final_output_manifest.json` を作り、保存済み file 一覧と canonical path を固定する。
5. cleanup は canonical tree を保持対象として明示し、それ以外の不可視中間生成物だけを削除候補へ載せる。
6. local zip や browser download は補助導線とし、失敗しても canonical tree が残ることを確認する。

## 必須確認

- final output tree の path が runbook context に入っている
- cleanup plan が final output tree を keep 対象に含む
- local-only file を削除しても final output の再解釈に必要な情報が Drive 側へ残る
- `final_output_manifest.json` が canonical path を返す

## 禁止

- final output を local zip 作成後に初めて保存する
- cleanup plan に final output tree を delete candidate として載せる
- final output の再解釈に必要な manifest / summary を local tmp にしか残さない
