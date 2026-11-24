"""The add-on's entry: what it hands `hero_hands.py`, where it finds AssetFurnace's own Python, and what it leaves
where the studio looks."""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import addon_run


def run_args(*rest):
    return ["blender", "-b", "--python", "addon_run.py", "--", "/o/run-1", "/m/hero_rigged.glb", "/p/hero.png", *rest]


def test_the_job_writes_the_glb_the_studio_looks_for():
    job = addon_run.plan(run_args("mirror"))
    assert job.result == Path("/o/run-1/run-1.glb")
    assert job.work == Path("/o/run-1/work")
    assert job.made == Path("/o/run-1/work/hero_rigged_hands.glb")  # hero_hands.py names it after the model
    assert job.argv[:2] == [str(Path("/m/hero_rigged.glb")), str(Path("/p/hero.png"))]
    assert job.argv[job.argv.index("--out") + 1] == str(Path("/o/run-1/work"))


def test_the_left_hand_choice():
    assert addon_run.plan(run_args("mirror")).argv[-2:] == ["--left", "mirror"]
    assert addon_run.plan(run_args("own")).argv[-2:] == ["--left", "own"]
    with pytest.raises(SystemExit):
        addon_run.plan(run_args("both"))


@pytest.mark.parametrize("blank", ["", "  ", "-", "none", "As in the picture"])
def test_a_blank_look_keeps_the_pictures_own(blank):
    assert "--look" not in addon_run.plan(run_args("mirror", blank)).argv


def test_a_look_in_words_reaches_the_drawing():
    argv = addon_run.plan(run_args("mirror", " black fingerless gloves ")).argv
    assert argv[argv.index("--look") + 1] == "black fingerless gloves"


def test_too_few_arguments_stop_with_the_usage():
    with pytest.raises(SystemExit, match="usage"):
        addon_run.plan(["--", "/o/run-1", "/m/a.glb"])


def test_the_manifest_offers_what_the_runner_takes():
    manifest = json.loads((HERE / "addon.json").read_text(encoding="utf-8"))
    (tool,) = manifest["tools"]
    inputs = {i["id"]: i for i in tool["inputs"]}
    assert tuple(inputs["left"]["choices"]) == addon_run.LEFT
    run = tool["run"]
    after = run[run.index("--") + 1:]
    assert after == ["{out}", "{model}", "{picture}", "{left}", "{look}"]
    assert run[run.index("--python") + 1] == "addon_run.py"
    assert tool["makes"] == "glb"


def test_the_manifest_names_every_model_it_runs_with_its_licence():
    manifest = json.loads((HERE / "addon.json").read_text(encoding="utf-8"))
    names = " ".join(m["name"] for m in manifest["models"])
    for model in ("FLUX.2 [klein]", "Pixal3D", "Real-ESRGAN"):
        assert model in names
    assert all(m["licence"] and "downloads nothing" in m["size"] for m in manifest["models"])


def an_install(folder):
    (folder / "image_to_3dlab").mkdir(parents=True)
    (folder / "scripts").mkdir()
    python = folder / ".venv" / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.write_text("")
    return python


def test_python_from_the_install_next_to_the_addon(tmp_path):
    root = tmp_path / "AssetFurnace"
    python = an_install(root)
    addon = root / "addons" / "hero-hands"
    addon.mkdir(parents=True)
    assert addon_run.find_python(addon, {}) == (python, root)


def test_python_named_by_i2l_python_wins(tmp_path):
    root = tmp_path / "AssetFurnace"
    an_install(root)
    other = tmp_path / "py" / "python.exe"
    other.parent.mkdir()
    other.write_text("")
    assert addon_run.find_python(root / "addons" / "hero-hands", {"I2L_PYTHON": str(other)}) == (other, root)


def test_an_addon_kept_elsewhere_runs_with_the_install_its_python_belongs_to(tmp_path):
    # installed into a folder of its own (a test, or a second copy) and started with I2L_PYTHON naming an install's
    # Python: a folder called addons that is no install must not count as one
    root = tmp_path / "AssetFurnace"
    python = an_install(root)
    addon = tmp_path / "scratch" / "addons" / "hero-hands"
    addon.mkdir(parents=True)
    assert addon_run.find_python(addon, {"I2L_PYTHON": str(python)}) == (python, root)


def test_no_python_found(tmp_path):
    assert addon_run.find_python(tmp_path / "somewhere", {}) == (None, None)


def test_a_python_outside_any_install_has_no_root(tmp_path):
    other = tmp_path / "py" / "Scripts" / "python.exe"
    other.parent.mkdir(parents=True)
    other.write_text("")
    assert addon_run.find_python(tmp_path / "somewhere", {"I2L_PYTHON": str(other)}) == (other, None)


def test_hand_over_copies_the_figure_and_its_numbers(tmp_path):
    job = addon_run.plan(["--", str(tmp_path / "run-1"), "/m/hero_rigged.glb", "/p/hero.png", "mirror"])
    job.work.mkdir(parents=True)
    job.made.write_bytes(b"glTF")
    (job.work / "hands.json").write_text("{}")
    assert addon_run.hand_over(job) == 0
    assert (tmp_path / "run-1" / "run-1.glb").read_bytes() == b"glTF"
    assert (tmp_path / "run-1" / "run-1.hands.json").is_file()


def test_hand_over_fails_when_no_figure_was_written(tmp_path, capsys):
    job = addon_run.plan(["--", str(tmp_path / "run-1"), "/m/hero_rigged.glb", "/p/hero.png", "mirror"])
    assert addon_run.hand_over(job) == 1
    assert "was not written" in capsys.readouterr().out
    assert not (tmp_path / "run-1" / "run-1.glb").exists()
