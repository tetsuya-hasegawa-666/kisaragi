---
name: document-topology-keeper
description: workspace または project の文書変更を見直し、内容を統合、削除、移動、分離のどれにするべきか判断する。新しい文書を追加する前、process rule を増やす前、同じ rule を複数 file に繰り返す前、または docs、develop、index、agent instruction を編集して文書重複が生じうるときに使う。
---

# Document Topology Keeper

## 適用境界

- この skill は documentation topology、authoritative file の配置、pointer の削減、重複除去に使う。
- archive のローテーションや version 付き legacy 移行を主目的にするときの第一選択にはしない。
- code や会話変更後の同一 turn 内 drift 検知を主目的にするときの第一選択にはしない。

workspace または project の文書を変更する前に使う。

## コアルール

同じ rule、status、guidance が近くにあるか確認する前に、文書を追加したり膨らませたりしない。
重複した要約を増やすより、明確な正本 1 つと明確な入口 1 つを優先する。

## 確認質問

1. この追加内容は、別の source-of-truth file、process file、index、agent file に既に存在しないか。
2. 新しい section や file を作るより、既存 section を更新すべきではないか。
3. 重複が必要な場合、それぞれが正本、入口、current status など異なる役割を持っているか。
4. 今回の変更後に削除または縮小できる古い section や file はないか。
5. 生成物は project 本体ではなく `test_field/` に置くべきではないか。

## 手順

1. 提案されている文書変更を特定する。
2. その topic に最も近い index、agent file、source-of-truth file を読む。
3. 対象 edit と既存文書の重複を列挙する。
4. 最小の妥当 topology を選ぶ。
   - 既存 section 1 つを更新する
   - 入口 file に短い pointer を 1 つ足す
   - 既存 file に吸収できない場合だけ新 file を作る
5. 可能なら同一 turn で stale duplicate text を削るか縮める。
6. 生成物が関係する場合、source-of-truth または runtime 必須 file でない限り `test_field/` に置く。
7. 編集後、どの file が authoritative で、どの file が pointer かを確認する。

## 運用ルール

- index は短く navigation に徹する
- process rule は process file に置き、status file には一時 pointer だけを残す
- current-state file は current status、blocker、next check に集中させる
- plan file は release 構造と execution record に集中させる
- 同じ rule を top-level agent file と下位文書の両方に置く場合、詳細は下位文書、短い強制文だけを agent file に置く
- 数 bullet しかない新 file が既存 file に収まるなら統合する
- 2 つの file が同じ目的へ寄ってきたら、どちらかを統合する

## 必須出力

文書 edit の前後で、少なくとも次を明示する。

- authoritative file
- 短い mention だけ残す pointer file
- 削除または縮小できる file / section
- `test_field/` へ移すべき生成物があるか
