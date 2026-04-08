#No: #7matching-1
前: #7-1..#7-3
次: #8-1..#8-2

# 7matching Overlap Pose Matching

この markdown cell は `#7matching-1` の overlap pose matching を説明する。
2 chunk の `pred_extrinsics.npy` と `chunk_input_frames.csv` を入力にし、共通 `record_index` を overlap 区間として抽出し、2 軌跡を同じ座標系へ再現する。
ここでは overlap 上の `scale`、`rotation`、`translation`、`relative_rotation_deg` を解き、可視化と residual 検証を同じ stage で残す。出力は `overlap_pair_metrics_arc.csv`、`trajectory_points_arc.csv`、`transform_b_to_a.npy`、`trajectory_match.png`、`trajectory_match.html`、`matching_summary.json` である。
入力 path は config の explicit path を優先し、未指定時は `final_outputs/chunk_evidence/<chunk_name>/`、ついで `chunk_runs/batch_*/<chunk_name>/` から自動解決する。既定 chunk pair は `MATCHING_CHUNK_IDS_1BASED=[6,7]` を使う。
