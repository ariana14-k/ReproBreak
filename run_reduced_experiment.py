"""Reduced-scope validation of the reproducible locator breaks.

Runs a curated subset of the 449 locator breaks (default: 8 breaks, two
per reproduced project, where each pair shares a commit so the Docker
image of a project is only built once) in both execution modes:

- fixed:            the test runs with the new locator  -> expected PASSED
- reproduce_break:  the old locator is reinserted       -> expected FAILED

A break is validated when both expectations hold. This is the reduced
experiment scope for artifact evaluation; the full scope (--all) runs
all 449 breaks and takes several days.

Usage:
    python run_reduced_experiment.py                 # curated subset (~1-3 h)
    python run_reduced_experiment.py --ids 1224 1225 # custom subset
    python run_reduced_experiment.py --all           # full scope (days)
"""
import argparse
import sqlite3
import sys
import time

from config import LB_PATH, REPRODUCTION_PATH
from create_reproducible_dataset import TestStatus
from reproduce import Reproduction_Mode, reproduce_locator_break

# Two breaks per reproduced project; each pair shares a commit, so each
# project's Docker image is built once and reused. 1224 is the example
# used in the paper (Figure 4).
CURATED_IDS = [1224, 1225, 616, 619, 3316, 3318, 5609, 5620]

EXPECTED = {
    Reproduction_Mode.FIXED.value: TestStatus.PASSED,
    Reproduction_Mode.REPRODUCE_BREAK.value: TestStatus.FAILED,
}


def get_repositories(db_path, ids):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    placeholders = ",".join("?" for _ in ids)
    cur.execute(f"SELECT id, repository_name FROM locator_change WHERE id IN ({placeholders})", ids)
    repositories = dict(cur.fetchall())
    con.close()
    return repositories


def get_all_break_ids(db_path):
    """All reproducible break IDs, ordered so that image reuse is maximized."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""SELECT lc.id
                   FROM locator_break lb
                   INNER JOIN locator_change lc ON lb.locator_change_id = lc.id
                   ORDER BY lc.repository_name, lc.commit_sha, lc.id""")
    ids = [row[0] for row in cur.fetchall()]
    con.close()
    return ids


def main():
    parser = argparse.ArgumentParser(description="Validate a set of reproducible locator breaks")
    parser.add_argument("--ids", type=int, nargs="+",
                        help=f"Locator break IDs to validate (default: curated subset {CURATED_IDS})")
    parser.add_argument("--all", action="store_true",
                        help="Validate all 449 breaks (full scope, takes several days)")
    parser.add_argument("--db", default=LB_PATH, help="Path to SQLite database")
    parser.add_argument("--work_dir", default=REPRODUCTION_PATH, help="Working directory for reproduction")
    args = parser.parse_args()

    if args.all:
        ids = get_all_break_ids(args.db)
    else:
        ids = args.ids if args.ids else CURATED_IDS

    repositories = get_repositories(args.db, ids)
    modes = [Reproduction_Mode.FIXED.value, Reproduction_Mode.REPRODUCE_BREAK.value]
    total_runs = len(ids) * len(modes)

    print("=" * 70)
    print(f"  Reduced experiment: validating {len(ids)} locator breaks ({total_runs} test runs)")
    print("=" * 70)

    results = []
    run_number = 0
    for locator_id in ids:
        for mode in modes:
            run_number += 1
            expected = EXPECTED[mode]
            print(f"\n[{run_number}/{total_runs}] break {locator_id} ({repositories.get(locator_id, '?')}), "
                  f"mode={mode}, expected={expected.value}")
            start = time.time()
            actual = reproduce_locator_break(locator_id, mode, args.db, args.work_dir)
            elapsed = time.time() - start
            ok = actual == expected
            results.append((locator_id, mode, expected, actual, ok, elapsed))
            print(f"[{run_number}/{total_runs}] -> {actual.value if actual else 'setup failed'} "
                  f"({'as expected' if ok else 'UNEXPECTED'}, {elapsed:.0f}s)")

    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"{'break':>7} {'repository':<30} {'mode':<16} {'expected':<9} {'actual':<15} {'result'}")
    validated = 0
    for locator_id, mode, expected, actual, ok, elapsed in results:
        actual_value = actual.value if actual else "setup failed"
        print(f"{locator_id:>7} {repositories.get(locator_id, '?'):<30} {mode:<16} "
              f"{expected.value:<9} {actual_value:<15} {'OK' if ok else 'FAIL'}")
        validated += ok

    breaks_ok = sum(
        1 for locator_id in ids
        if all(ok for lid, _, _, _, ok, _ in results if lid == locator_id)
    )
    print(f"\n{validated}/{total_runs} runs behaved as expected; "
          f"{breaks_ok}/{len(ids)} breaks fully validated (pass with new locator, fail with old).")

    if validated != total_runs:
        sys.exit(1)


if __name__ == "__main__":
    main()
