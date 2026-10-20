#!/usr/bin/env python3
"""Strict pre-commit and pre-push security scanner.

Scans the repository to prevent any sensitive credentials, tokens, or private keys
from ever being committed or pushed to Git.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# Directories and files to ignore during scan
IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "backups",
}

IGNORE_FILES = {
    ".gitignore",
    ".env.example",
    "security_check.py",
}

# Regex patterns that indicate potential secrets
SECRET_PATTERNS = [
    (
        "Telegram Bot Token",
        re.compile(r"\b[0-9]{8,12}:[a-zA-Z0-9_-]{30,40}\b"),
    ),
    (
        "OpenAI API Key",
        re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"),
    ),
    (
        "Google Cloud / Gemini API Key",
        re.compile(r"\bAIza[0-9A-Za-z-_]{35}\b"),
    ),
    (
        "GitHub Personal Access Token",
        re.compile(r"\bgh[pousr]_[0-9a-zA-Z]{36}\b"),
    ),
    (
        "Private Key Header",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ),
    (
        "Hardcoded Secret Assignment",
        re.compile(r"""(?i)(bot_token|secret_key|api_key|password)\s*=\s*['\"][0-9a-zA-Z_\-]{16,}['\"]"""),
    ),
]


def check_git_tracked_files() -> list[str]:
    """Ensures no real .env or SQLite databases are tracked by git."""
    errors = []
    try:
        tracked = subprocess.check_output(
            ["git", "ls-files"], text=True
        ).splitlines()
        for file in tracked:
            if file == ".env" or (file.startswith(".env.") and file != ".env.example"):
                errors.append(f"CRITICAL: Sensitive environment file tracked in git: {file}")
            if file.endswith(".db") or file.endswith(".sqlite3") or file.endswith("-wal") or file.endswith("-shm"):
                errors.append(f"CRITICAL: Database file tracked in git: {file}")
    except Exception as exc:
        errors.append(f"Failed to check git tracked files: {exc}")
    return errors


def scan_file(file_path: Path) -> list[str]:
    """Scans an individual file line by line for secrets."""
    errors = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                # Skip comments or documentation references if harmless
                for name, pattern in SECRET_PATTERNS:
                    match = pattern.search(line)
                    if match:
                        matched_val = match.group(0)
                        # Exclude harmless test mock words
                        if "mock" in matched_val.lower() or "dummy" in matched_val.lower():
                            continue
                        errors.append(
                            f"[{name}] in {file_path}:{line_no} -> Found matching pattern: '{matched_val[:4]}...{matched_val[-4:]}'"
                        )
    except Exception as exc:
        errors.append(f"Could not read {file_path}: {exc}")
    return errors


def main() -> int:
    """Executes full repository security audit."""
    print("=" * 60)
    print("🔍 RUNNING PRE-COMMIT / PRE-PUSH SECURITY SCANNER")
    print("=" * 60)

    repo_root = Path(__file__).resolve().parent.parent
    all_errors = []

    # 1. Check Git tracked files
    tracked_errors = check_git_tracked_files()
    if tracked_errors:
        all_errors.extend(tracked_errors)

    # 2. Scan all files in repository
    files_scanned = 0
    for root, dirs, files in os.walk(repo_root):
        # Exclude ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in IGNORE_FILES or file.startswith(".env"):
                continue
            file_path = Path(root) / file
            file_errors = scan_file(file_path)
            if file_errors:
                all_errors.extend(file_errors)
            files_scanned += 1

    print(f"Scanned {files_scanned} files across repository.")

    if all_errors:
        print("\n❌ SECURITY SCAN FAILED! Sensitive data or tokens detected:\n")
        for err in all_errors:
            print(f"  • {err}")
        print("\nCommit and push ABORTED. Remove all secrets before proceeding!\n")
        return 1

    print("✅ SECURITY SCAN PASSED! No sensitive secrets or tokens detected.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
