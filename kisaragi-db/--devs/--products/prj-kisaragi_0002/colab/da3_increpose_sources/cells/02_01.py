#2-1
from pathlib import Path
import json
import pandas as pd
from IPython.display import display

CONFIG = {
    "PROJECT_SLUG": "da3_ngl_run_v01",
    "PIPELINE_SLUG": "da3_ngl_batch_v01",
    "MODEL_ID": "depth-anything/DA3NESTED-GIANT-LARGE-1.1",
    "BUNDLE_MODEL_SLUG": "nestedgiantlarge11",
    "BATCH_SIZE": 2,
    "CHUNK_SIZE": 18,
    "CHUNK_STEP": 6,
    "CONTEXT_SIZE": 12,
    "OUTPUT_SIZE": 6,
    "ADOPT_SIZE": 6,
    "TEST_TOTAL_FRAMES": 36,
    "PROCESS_RES": 504,
    "PROCESS_RES_METHOD": "upper_bound_resize",
    "DEVICE": "cuda",
    "EXPORT_FORMAT": "npz-glb-gs_ply-gs_video",
    "ALIGN_TO_INPUT_EXT_SCALE": True,
    "INFER_GS": True,
    "SHOW_CAMERAS": False,
    "CONF_THRESH_PERCENTILE": 40.0,
    "NUM_MAX_POINTS": 1000000,
    "SKIP_ALREADY_SUCCESS": True,
    "RESET_TARGET_OUTPUTS_BEFORE_RUN": True,
    "MAKE_DRIVE_BUNDLE": False,
    "DOWNLOAD_LOCAL_BUNDLE": False,
    "TARGET_CHUNK_MODE": "selected_chunk_ids_1based",
    "TARGET_CHUNK_IDS_1BASED": [6, 7],
    "MATCHING_CHUNK_IDS_1BASED": [6, 7],
    "MATCHING_CHUNK_A_NAME": "",
    "MATCHING_CHUNK_B_NAME": "",
    "MATCHING_CHUNK_A_INPUT_FRAMES_PATH": "",
    "MATCHING_CHUNK_A_PRED_EXTRINSICS_PATH": "",
    "MATCHING_CHUNK_B_INPUT_FRAMES_PATH": "",
    "MATCHING_CHUNK_B_PRED_EXTRINSICS_PATH": "",
    "USE_TARGET_CHUNK_WINDOW": False,
    "TARGET_CHUNK_WINDOW_START_1BASED": 1,
    "TARGET_CHUNK_WINDOW_COUNT": 0,
    "ROLL_BAND_DEG": 20.0,
    "PITCH_MIN_DEG": -85.0,
    "PITCH_MAX_DEG": -1.0,
    "YAW_JUMP_MAX_DEG": 90.0,
    "ANCHOR_QC_WARN_ABS_ROLL_CENTERED_DEG": 15.0,
    "ANCHOR_QC_WARN_PITCH_MIN_DEG": -89.0,
    "ANCHOR_QC_WARN_PITCH_MAX_DEG": 89.0,
    "ANCHOR_QC_MAX_DELTA_LENS_ANGLE_DEG": 45.0,
    "AUTO_SELECT_SESSION_ID": "",
    "AUTO_SELECT_CANDIDATE_INDEX": None,
    "AUTO_SELECT_POLICY": "latest_modified",
    "POSE_PIPELINE_MODE": "sliding_window_incremental_seeded",
    "OVERLAP_SIZE": 12,
    "SEED_USE_PREV_POSE": True,
    "EVAL_ONLY_OUTPUT_RANGE": True,
    "OUTPUT_START_LOCAL_IDX": 12,
    "OUTPUT_END_LOCAL_IDX": 18,
}
assert CONFIG["CHUNK_SIZE"] == CONFIG["CONTEXT_SIZE"] + CONFIG["OUTPUT_SIZE"], CONFIG
assert CONFIG["CHUNK_STEP"] == CONFIG["OUTPUT_SIZE"] == CONFIG["ADOPT_SIZE"], CONFIG
assert CONFIG["OVERLAP_SIZE"] == CONFIG["CHUNK_SIZE"] - CONFIG["CHUNK_STEP"], CONFIG
assert CONFIG["OUTPUT_START_LOCAL_IDX"] == CONFIG["CONTEXT_SIZE"], CONFIG
assert CONFIG["OUTPUT_END_LOCAL_IDX"] == CONFIG["CHUNK_SIZE"], CONFIG

Path('/content/config_snapshot.json').write_text(json.dumps(CONFIG, indent=2, ensure_ascii=False), encoding='utf-8')
display(pd.DataFrame([{"item": k, "value": str(v)} for k, v in CONFIG.items()]))
