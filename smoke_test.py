"""Smoke test for the ReproBreak artifact.

Verifies in under a minute that the environment is ready to use the
artifact: Python dependencies import, the git CLI is available, the
dataset is present with the expected row counts, and the Docker daemon
is reachable.

Usage:
    python smoke_test.py [--db data/ReproBreak.db] [--skip-docker]
"""
import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path

from config import LB_PATH

EXPECTED_COUNTS = {
    "repository": 359,
    "locator_change": 9572,
    "locator_break": 449,
    "reproduce_files": 8,
}


def check(label, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    suffix = f" ({detail})" if detail else ""
    print(f"  [{mark}] {label}{suffix}")
    return ok


def check_dependencies():
    ok = True
    print("Python dependencies")
    for module in ("docker", "git", "unidiff", "tqdm", "pandas"):
        try:
            __import__(module)
            ok &= check(f"import {module}", True)
        except ImportError as e:
            ok &= check(f"import {module}", False, str(e))
    return ok


def check_git():
    print("Git CLI")
    try:
        version = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
        return check("git available", True, version.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        return check("git available", False, str(e))


def check_database(db_path):
    print("Dataset")
    if not check(f"database file exists: {db_path}", Path(db_path).exists()):
        return False

    ok = True
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    for table, expected in EXPECTED_COUNTS.items():
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            ok &= check(f"{table}: {count} rows", count == expected, f"expected {expected}")
        except sqlite3.Error as e:
            ok &= check(f"{table}", False, str(e))
    con.close()
    return ok


def check_docker():
    print("Docker")
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return check("Docker daemon reachable", True)
    except Exception as e:
        return check("Docker daemon reachable", False, str(e))


def main():
    parser = argparse.ArgumentParser(description="ReproBreak artifact smoke test")
    parser.add_argument("--db", default=LB_PATH, help="Path to SQLite database")
    parser.add_argument("--skip-docker", action="store_true",
                        help="Skip the Docker daemon check (validates the dataset only)")
    args = parser.parse_args()

    print("=" * 50)
    print("  ReproBreak smoke test")
    print("=" * 50)

    ok = check_dependencies()
    ok &= check_git()
    ok &= check_database(args.db)
    if not args.skip_docker:
        ok &= check_docker()

    print("=" * 50)
    if ok:
        print("SMOKE TEST PASSED")
    else:
        print("SMOKE TEST FAILED (see [FAIL] lines above)")
        sys.exit(1)


if __name__ == "__main__":
    main()
