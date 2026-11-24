"""The launcher puts the add-on's scripts first, lends the hand module to AssetFurnace's own package and points
`hero_hands.py` at the install's tools."""

import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import launcher


def test_paths_put_the_addon_first_and_the_install_after(tmp_path, monkeypatch):
    root = tmp_path / "AssetFurnace"
    (root / "scripts").mkdir(parents=True)
    path = ["site-packages"]
    monkeypatch.setattr(sys, "path", path)
    launcher.set_paths(root)
    assert path[0] == str(HERE / "scripts")
    assert path.index(str(root)) < path.index("site-packages")
    assert path.index(str(root / "viewer")) < path.index("site-packages")  # the picture editor's command builder
    assert path.index(str(root / "scripts")) > path.index(str(HERE / "scripts"))


def test_the_hand_module_joins_the_installed_package(monkeypatch):
    package = types.ModuleType("image_to_3dlab")
    package.__path__ = ["/install/image_to_3dlab"]
    monkeypatch.setitem(sys.modules, "image_to_3dlab", package)
    launcher.lend_module()
    assert package.__path__ == ["/install/image_to_3dlab", str(HERE / "extra")]
    launcher.lend_module()  # twice changes nothing
    assert package.__path__.count(str(HERE / "extra")) == 1


def test_the_lent_module_is_the_hand_module_only():
    """When AssetFurnace ships it itself, its own copy wins: the install's folder comes first."""
    assert sorted(p.name for p in (HERE / "extra").glob("*.py")) == ["hero_hands.py"]


def test_the_script_runs_the_installs_tools(tmp_path):
    # hero_hands.py names Pixal3D's command, the upscaler and its default output folder from its own folder, as it
    # does inside AssetFurnace; in an add-on that folder is the add-on's, which has neither
    script = types.SimpleNamespace(REPO=HERE, GENERATE=HERE / "scripts" / "pixal3d_generate.py",
                                   UPSCALE=HERE / "scripts" / "upscale_esrgan.py")
    launcher.point_at_install(script, tmp_path)
    assert script.REPO == tmp_path
    assert script.GENERATE == tmp_path / "scripts" / "pixal3d_generate.py"
    assert script.UPSCALE == tmp_path / "scripts" / "upscale_esrgan.py"


def test_every_name_the_launcher_points_is_one_the_script_has():
    text = (HERE / "scripts" / "hero_hands.py").read_text(encoding="utf-8")
    for name in ("REPO", "GENERATE", "UPSCALE"):
        assert f"\n{name} = " in text
