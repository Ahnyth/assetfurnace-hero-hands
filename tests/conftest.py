"""The entry and launcher tests run anywhere. The hand module's own tests (`test_hero_hands*.py`, the same as on the
fork branch these scripts come from) need AssetFurnace's package and scripts: name the install with `I2L_ROOT` and run
them with its Python (`<install>/.venv/Scripts/python -m pytest tests`), or they are skipped."""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ["I2L_ROOT"]).resolve() if os.environ.get("I2L_ROOT") else None

collect_ignore = []
if ROOT is None or not (ROOT / "image_to_3dlab").is_dir():
    collect_ignore = ["test_hero_hands.py", "test_hero_hands_script.py"]
else:
    sys.path[:0] = [str(HERE), str(ROOT), str(ROOT / "viewer"), str(ROOT / "scripts")]
    import launcher

    launcher.lend_module()
    import scripts.hero_hands as script

    launcher.point_at_install(script, ROOT)
