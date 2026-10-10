"""Key-like strings that must never be written to a note or committed (design §12.1).

Built-in patterns cover the common credential formats; `gitleaks` is used in
addition when it is installed, never as a hard dependency.
"""

import re
import shutil
import subprocess

PATTERNS = {
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
    "API secret key (sk-…)": re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{32,}"),
    "Stripe live key": re.compile(r"\b[rs]k_live_[A-Za-z0-9]{20,}"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "private key": re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----"),
}


def _gitleaks(text: str) -> bool:
    """True when gitleaks is installed and reports a leak in `text`."""
    exe = shutil.which("gitleaks")
    if exe is None:
        return False
    try:
        r = subprocess.run([exe, "stdin", "--no-banner", "--redact", "--exit-code", "3"],
                           input=text, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 3


def find_secrets(text: str, original: str | None = None, use_gitleaks: bool = True) -> list[tuple[int, str]]:
    """(1-based line number, kind) for every key-like string in `text`.

    With `original`, only lines that are not already there are checked, so an
    old note never blocks appending to it. A finding reported only by gitleaks
    has line number 0.
    """
    old = set(original.splitlines()) if original is not None else set()
    new = [(n, line) for n, line in enumerate(text.splitlines(), 1) if line not in old]
    found = [(n, kind) for n, line in new for kind, pattern in PATTERNS.items() if pattern.search(line)]
    if not found and new and use_gitleaks and _gitleaks("\n".join(line for _, line in new)):
        found.append((0, "secret reported by gitleaks"))
    return found
