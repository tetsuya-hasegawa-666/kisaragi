#9-3
from pathlib import Path
import json

config = json.loads(Path('/content/config_snapshot.json').read_text(encoding='utf-8'))
config_view = pd.DataFrame([
    {'item': 'BATCH_SIZE', 'value': config['BATCH_SIZE']},
    {'item': 'CHUNK_SIZE', 'value': config['CHUNK_SIZE']},
    {'item': 'CHUNK_STEP', 'value': config['CHUNK_STEP']},
    {'item': 'ADOPT_SIZE', 'value': config['ADOPT_SIZE']},
    {'item': 'PROCESS_RES', 'value': config['PROCESS_RES']},
])
display(config_view)
display_stage_summary(
    "9-3",
    "config snapshot preview",
    inputs=[
        {"item": "config_snapshot", "path": "/content/config_snapshot.json"},
    ],
    outputs=[],
    notes=config_view.to_dict(orient='records'),
)
