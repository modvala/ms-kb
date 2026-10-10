"""A LaunchAgent that runs `kb sync` hourly on macOS (design §12.3).

`StartCalendarInterval` plus `RunAtLoad`: runs missed during sleep are
coalesced into one on wake. Installed only with the user's consent and
recorded in installed.toml, so only kb's own agent is ever replaced or removed.
"""

import os
import plistlib
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from ms_kb import __version__
from ms_kb.installer import display, load_state, save_state

LABEL = "io.github.modvala.ms-kb.sync"
PATH = "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin"


def supported() -> bool:
    return sys.platform == "darwin"


def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def log_path() -> Path:
    return Path.home() / "Library" / "Logs" / "ms-kb" / "sync.log"


def launchctl(*args: str) -> subprocess.CompletedProcess:
    """The only call into launchd; tests replace it."""
    return subprocess.run(["launchctl", *args], capture_output=True, text=True)


def _domain() -> str:
    return f"gui/{os.getuid()}"


def kb_executable() -> str:
    """The installed `kb`, as an absolute path: launchd has no PATH of the user's shell."""
    found = shutil.which("kb")
    if found:
        return str(Path(found).resolve())
    return str(Path(sys.argv[0]).resolve())


def plist(kb: str) -> dict:
    env = {"PATH": f"{Path(kb).parent}:{PATH}"}
    if config := os.environ.get("KB_CONFIG"):
        env["KB_CONFIG"] = str(Path(config).expanduser().resolve())
    log = str(log_path())
    return {
        "Label": LABEL,
        "ProgramArguments": [kb, "sync", "--quiet"],
        "StartCalendarInterval": {"Minute": 0},
        "RunAtLoad": True,
        "ProcessType": "Background",
        "EnvironmentVariables": env,
        "StandardOutPath": log,
        "StandardErrorPath": log,
    }


def installed() -> bool:
    return "schedule" in load_state() and plist_path().is_file()


def loaded() -> bool:
    return launchctl("print", f"{_domain()}/{LABEL}").returncode == 0


def install(kb: str | None = None) -> list[str]:
    """Write the plist and (re)load it. Returns report lines; raises OSError/RuntimeError."""
    if not supported():
        raise RuntimeError("the hourly schedule uses launchd and is available on macOS only; "
                           "run kb sync from cron or by hand")
    kb = kb or kb_executable()
    path = plist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    log_path().parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    with path.open("wb") as f:
        plistlib.dump(plist(kb), f)
    launchctl("bootout", f"{_domain()}/{LABEL}")
    r = launchctl("bootstrap", _domain(), str(path))
    if r.returncode != 0:
        raise RuntimeError(f"launchctl bootstrap failed: {(r.stderr or r.stdout).strip()}")
    state = load_state()
    state["schedule"] = {"label": LABEL, "plist": display(path), "kb": kb,
                         "package_version": __version__, "installed": date.today().isoformat()}
    save_state(state)
    return [f"{'updated' if existed else 'installed'} {display(path)} (kb sync hourly; log: {display(log_path())})"]


def remove() -> list[str]:
    state = load_state()
    if "schedule" not in state:
        return ["no schedule installed by kb"]
    launchctl("bootout", f"{_domain()}/{LABEL}")
    path = plist_path()
    if path.exists():
        path.unlink()
    del state["schedule"]
    save_state(state)
    return [f"removed {display(path)}"]


def status() -> list[str]:
    if not supported():
        return ["schedule: not supported on this system (macOS launchd only)"]
    if not installed():
        return ["schedule: not installed (kb sync --schedule on)"]
    entry = load_state()["schedule"]
    return [f"schedule: {'loaded' if loaded() else 'NOT loaded'}, {entry['plist']}, runs {entry['kb']} sync hourly",
            f"log: {display(log_path())}"]


def time_machine_latest() -> str | None:
    """The latest Time Machine backup, or None when unknown (not configured or not allowed to answer)."""
    if not supported():
        return None
    try:
        r = subprocess.run(["tmutil", "latestbackup"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = r.stdout.strip()
    return out.rsplit("/", 1)[-1] if r.returncode == 0 and out else None
