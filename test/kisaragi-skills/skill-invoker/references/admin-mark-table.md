# admin mark table

## 目的

- admin の短い mark を `skill-invoker` が一貫して解釈するための定義表とする。

## mark 一覧

| mark | 意味 | distributor の処理 |
| --- | --- | --- |
| `//s` | code と文書と記録を同 task でそろえる | planner へ同期強制を付ける |
| `//d` | 依存、path、artifact、directory を棚卸しする | planner へ依存棚卸し強制を付ける |
| `//c` | この点は admin が確認したい | plan に確認待ち論点を残す |
| `//m` | この処理は必須 | 対象処理を省略不可にする |
| `//x` | 文脈固定を強める | minimum docs を広げる |
| `//l` | 今回は log 優先でよい | 正本昇格を保留候補として扱う |
| `//p` | 正本へ昇格する | 正本更新を省略不可にする |
| `//g` | shared rule 変更を含む | `AGENTS.md` と `AGENTSmd-RH.md` の確認を追加する |

## 運用原則

- mark は optional trigger であり、常用必須ではない。
- mark が無くても通常 rule で文書読込、更新、test、記録反映は動く。
- mark がある時だけ、追加の強制動作を planner と specialist に付与する。



