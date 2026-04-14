# skill direct gap list

| 対象 | 直指示度 | 現状 route | gap |
| --- | --- | --- | --- |
| 原本全文と refresh 全文の完全 diff 監査 | C | 原本 snapshot 比較 | exhaustive audit skill 不在 |
| temp archive から canonical 本文への段落再配線 | C | `documentation-watchkeeper` + 手動判断 | 吸収基準が project 固有 |
| DA 表の圧縮最適化 | C | 手動整形 | table formatter skill 不在 |
| shared worklog 50k rotate 実施 | B | `log-promotable-facts-extractor` + 手動 rotate | rotate 専用 skill 不在 |
| `p-done` / `i-pass` 根拠 row の表記正規化 | B | `test-and-evidence-recorder` + 手動整形 | evidence row formatter 不在 |
| refresh canonical と origin snapshot の双方向監査 | C | `doc-governor` 的運用 + 手動比較 | bidirectional audit skill 不在 |

- `A=既存 skill でほぼ完結`
- `B=既存 skill + 手動補助`
- `C=手動判断主体`
