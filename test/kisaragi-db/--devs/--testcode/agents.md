# agents.md

## --testcode の役割

- この階層は、project ごとの test code を保持する。

## 運用規則

- test code は `prj-<project名>/` 配下へ置く。
- test 実行で生成される raw file は `--exsams/` または ignore 対象へ逃がす。
- `Colab` artifact を手元で再解釈する `.py` や、正式 test command 相当の probe script も、この階層の test code 正本として管理する。
- 上記の script は、入力 artifact 実体や raw 出力を `--exsams/` に置き、code 自体は `--testcode/` に残す。
- `prj-kisaragi_0002` では camera pose convention probe の正式 script を `prj-kisaragi_0002/test_pose_convention_probe.py` として管理し、`colab-inputs/` に置くものは結果 summary か一時派生物だけにする。
