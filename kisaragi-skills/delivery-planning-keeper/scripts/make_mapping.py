#!/usr/bin/env python3
"""Create a simple TDD mapping skeleton from behavior IDs.
Usage: python make_mapping.py B1 B2 B3
"""
import sys

ids = sys.argv[1:]
print("| task_id | behavior_id | test_target | criterion | status | evidence |")
print("|---|---|---|---|---|---|")
for i, behavior_id in enumerate(ids, 1):
    print(f"| T{i} | {behavior_id} | TBD | TBD | planned | - |")
