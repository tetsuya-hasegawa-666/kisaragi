# handoff packet template

## 目的

- `skill-planner` から specialist skill へ渡す最小 handoff を統一する。

## template

```text
task_summary:
project_code:
target_paths:
must_read:
- ...
expected_result:
- ...
close_condition:
- ...
admin_marks:
- ...
notes:
- ...
```

## 必須項目

- `task_summary`
- `must_read`
- `expected_result`
- `close_condition`

## 原則

- specialist に発火判断は渡さない
- 何を読めばよいか、何を出せばよいかだけを明示する
