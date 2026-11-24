"""Run this add-on's `hero_hands.py` with the AssetFurnace install it lives in.

`addon_run.py` starts this file with the install's own Python. It puts the add-on's `scripts/` first on the path,
then the install's root (its `image_to_3dlab` package, ahead of any other copy in site-packages), its `viewer/` (the
picture editor's command builder) and its `scripts/` (the run log, the rig check, Pixal3D's command and the
upscaler). The hand module (`extra/hero_hands.py`) joins the installed `image_to_3dlab` package; a copy the core ships
itself comes first. `hero_hands.py` names its tools from its own folder, as it does inside AssetFurnace; here they are
the install's, so the launcher points it there.

    python launcher.py INSTALL_ROOT ARGS...
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def set_paths(root: Path) -> None:
    sys.path.insert(0, str(HERE / "scripts"))
    sys.path.insert(1, str(root))
    sys.path.insert(2, str(root / "viewer"))
    sys.path.insert(3, str(root / "scripts"))


def lend_module() -> None:
    import image_to_3dlab

    extra = str(HERE / "extra")
    if extra not in image_to_3dlab.__path__:
        image_to_3dlab.__path__.append(extra)


def point_at_install(module, root: Path) -> None:
    """The tools `hero_hands.py` runs (Pixal3D, the upscaler) and its default output folder are the install's."""
    module.REPO = root
    module.GENERATE = root / "scripts" / "pixal3d_generate.py"
    module.UPSCALE = root / "scripts" / "upscale_esrgan.py"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: launcher.py INSTALL_ROOT ARGS...")
        return 2
    root, rest = Path(argv[1]).resolve(), argv[2:]
    set_paths(root)
    lend_module()
    import hero_hands

    point_at_install(hero_hands, root)
    return hero_hands.main(rest)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
