"""AssetFurnace add-on entry: give a rigged figure hands with real fingers and leave `{out}/{stem}.glb`.

Runs inside Blender (the add-on's `run` starts `{blender}` with this file), so the studio only has to know Blender.
The work is done by `scripts/hero_hands.py`, which needs numpy, Pillow, SciPy, OpenCV and AssetFurnace's own package
and tools (Pixal3D, the picture editor, the upscaler), none of which Blender's Python has. So this file starts it with
the Python of the AssetFurnace install the add-on lives in (`<install>/.venv`; `I2L_PYTHON` names another one),
through `launcher.py`. Its steps write into `{out}/work` (the drawings, the hand builds, `run.log`, `hands.json`); the
figure with its new hands is copied to `{out}/{stem}.glb`, the name AssetFurnace looks for, and its numbers to
`{out}/{stem}.hands.json`.

    blender -b --factory-startup -P addon_run.py -- OUT_DIR MODEL PICTURE LEFT PAINT [LOOK]
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent

LEFT = ("mirror", "own")  # mirror: the left hand is the right one mirrored; own: drawn and built from its own crop
PAINT = ("match the figure", "as built")  # match: the new hands take the tone of their drawing, which was drawn to
# match the figure (Pixal3D's clean-up paints a built hand darker and far more saturated than its drawing); as built:
# left as it came
NO_LOOK = {"", "-", "none", "as in the picture"}


@dataclass
class Job:
    argv: list[str]  # for hero_hands.py
    work: Path  # hero_hands.py's run folder
    made: Path  # what hero_hands.py writes
    result: Path  # what AssetFurnace looks for


def _pick(name: str, value: str, choices: Sequence[str]) -> str:
    value = value.strip()
    if value not in choices:
        raise SystemExit(f"{name}: {value!r} is not one of {', '.join(choices)}")
    return value


def plan(argv: Sequence[str]) -> Job:
    """The job from the arguments after Blender's `--`."""
    args = list(argv[list(argv).index("--") + 1:] if "--" in argv else argv)
    if len(args) not in (5, 6):
        raise SystemExit("usage: addon_run.py -- OUT_DIR MODEL PICTURE LEFT PAINT [LOOK]")
    out_dir, model, picture = Path(args[0]), Path(args[1]), Path(args[2])
    left = _pick("left hand", args[3], LEFT)
    paint = "match" if _pick("hand paint", args[4], PAINT) == PAINT[0] else "keep"
    look = args[5].strip() if len(args) == 6 else ""
    stem = out_dir.name
    work = out_dir / "work"
    cmd = [str(model), str(picture), "--out", str(work), "--left", left, "--hand-paint", paint]
    if look.lower() not in NO_LOOK:
        cmd += ["--look", look]
    return Job(cmd, work, work / f"{model.stem}_hands.glb", out_dir / f"{stem}.glb")


def is_install(folder: Path | None) -> bool:
    return folder is not None and (folder / "image_to_3dlab").is_dir() and (folder / "scripts").is_dir()


def find_python(addon_dir: Path, env: Mapping[str, str]) -> tuple[Path | None, Path | None]:
    """(AssetFurnace's Python, the install's root): `I2L_PYTHON`, else the install's `.venv`, else an active venv.

    The root is the install the add-on lives in (`<install>/addons/hero-hands`); an add-on kept elsewhere and run with
    `I2L_PYTHON` uses the install that Python's venv belongs to (`<install>/.venv/Scripts/python.exe`)."""
    home = addon_dir.parent.parent if addon_dir.parent.name == "addons" else None
    candidates = []
    if env.get("I2L_PYTHON"):
        candidates.append(Path(env["I2L_PYTHON"]))
    if home is not None:
        candidates += [home / ".venv" / "Scripts" / "python.exe", home / ".venv" / "bin" / "python"]
    if env.get("VIRTUAL_ENV"):
        venv = Path(env["VIRTUAL_ENV"])
        candidates += [venv / "Scripts" / "python.exe", venv / "bin" / "python"]
    for candidate in candidates:
        if candidate.is_file():
            if is_install(home):
                return candidate, home
            venv_home = candidate.parent.parent.parent  # <install>/.venv/Scripts/python.exe
            return candidate, venv_home if is_install(venv_home) else None
    return None, home if is_install(home) else None


def hand_over(job: Job) -> int:
    """Copy hero_hands.py's figure and numbers to where AssetFurnace looks; 1 when it wrote no figure."""
    if not job.made.is_file():
        print(f"hero-hands: {job.made.name} was not written (see {job.work / 'run.log'})", flush=True)
        return 1
    shutil.copyfile(job.made, job.result)
    numbers = job.work / "hands.json"
    if numbers.is_file():
        shutil.copyfile(numbers, job.result.with_suffix(".hands.json"))
    return 0


def main(argv: Sequence[str]) -> int:
    import bpy  # only inside Blender: the path of the Blender that runs this file

    job = plan(argv)
    python, root = find_python(HERE, os.environ)
    if python is None or root is None:
        print("hero-hands: AssetFurnace's own Python was not found next to this add-on (<install>/.venv); "
              "set I2L_PYTHON to it", flush=True)
        return 1
    job.result.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "I2L_BLENDER": os.environ.get("I2L_BLENDER") or bpy.app.binary_path}
    cmd = [str(python), str(HERE / "launcher.py"), str(root), *job.argv]
    code = subprocess.run(cmd, cwd=str(HERE), env=env, check=False).returncode
    if code != 0:
        return code
    return hand_over(job)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
