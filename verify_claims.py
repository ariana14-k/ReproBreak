"""Regenerate the paper's headline numbers from the shipped database.

Recomputes, directly from data/ReproBreak.db, the dataset-scale numbers
and the derivable columns of Tables 1 and 2 of the ReproBreak paper, and
compares each against the value reported in the paper. Exits non-zero if
any check fails.

Not checked here (not stored in the database):
- Table 1 columns #Lc_valid (580) and #Lnb (131): the per-run Phase-2
  outputs are required; see README, "Claims not directly supported".
- Table 2 denominators (189/154/16 projects per framework): computed
  during Phase-1 test-file detection and not persisted per test file.

Usage:
    python verify_claims.py [--db data/ReproBreak.db]
"""
import argparse
import sqlite3
import sys

from config import LB_PATH

# Dataset-scale claims (abstract, Sections 2-3).
SCALE_CLAIMS = {
    "analyzed repositories": 359,
    "locator changes (#Lc)": 9572,
    "repositories with locator changes": 211,
    "reproducible locator breaks (#Lb)": 449,
}

# Table 2: locator changes and projects with changes, per framework class.
TABLE2_CLAIMS = {
    "playwright": (4186, 111),
    "cypress": (4026, 86),
    "both": (1360, 14),
}

# Table 1: #Lc and #Lb per reproduced project.
TABLE1_LC_CLAIMS = {
    "ghiscoding/angular-slickgrid": 344,
    "nasa/openmct": 271,
    "tryghost/koenig": 264,
    "microsoft/playwright": 399,
}
TABLE1_LB_CLAIMS = {
    "ghiscoding/angular-slickgrid": 258,
    "nasa/openmct": 48,
    "tryghost/koenig": 93,
    "microsoft/playwright": 50,
}


def report(rows):
    """Print claim rows as (name, paper value, database value) and return overall success."""
    ok = True
    for name, paper, db in rows:
        match = paper == db
        ok &= match
        mark = "PASS" if match else "FAIL"
        print(f"  [{mark}] {name}: paper={paper}, database={db}")
    return ok


def scale_rows(cur):
    queries = {
        "analyzed repositories": "SELECT COUNT(*) FROM repository",
        "locator changes (#Lc)": "SELECT COUNT(*) FROM locator_change",
        "repositories with locator changes": "SELECT COUNT(DISTINCT repository_name) FROM locator_change",
        "reproducible locator breaks (#Lb)": "SELECT COUNT(*) FROM locator_break",
    }
    return [(name, SCALE_CLAIMS[name], cur.execute(query).fetchone()[0]) for name, query in queries.items()]


def table2_rows(cur):
    """Classify each repository by the frameworks of its locator changes."""
    query = """
        WITH repo_fw AS (
            SELECT repository_name, GROUP_CONCAT(DISTINCT framework) fw, COUNT(*) lc
            FROM locator_change GROUP BY repository_name
        )
        SELECT CASE WHEN fw LIKE '%cypress%' AND fw LIKE '%playwright%' THEN 'both'
                    WHEN fw LIKE '%playwright%' THEN 'playwright'
                    ELSE 'cypress' END AS class,
               SUM(lc), COUNT(*)
        FROM repo_fw GROUP BY class
    """
    computed = {row[0]: (row[1], row[2]) for row in cur.execute(query)}
    rows = []
    for fw, (paper_lc, paper_projects) in TABLE2_CLAIMS.items():
        db_lc, db_projects = computed.get(fw, (0, 0))
        rows.append((f"Table 2 {fw}: #Lc", paper_lc, db_lc))
        rows.append((f"Table 2 {fw}: projects with Lc", paper_projects, db_projects))
    return rows


def table1_rows(cur):
    rows = []
    for repo, paper_lc in TABLE1_LC_CLAIMS.items():
        db_lc = cur.execute(
            "SELECT COUNT(*) FROM locator_change WHERE repository_name = ?", (repo,)
        ).fetchone()[0]
        rows.append((f"Table 1 {repo}: #Lc", paper_lc, db_lc))
    for repo, paper_lb in TABLE1_LB_CLAIMS.items():
        db_lb = cur.execute(
            """SELECT COUNT(*) FROM locator_break lb
               JOIN locator_change lc ON lb.locator_change_id = lc.id
               WHERE lc.repository_name = ?""", (repo,)
        ).fetchone()[0]
        rows.append((f"Table 1 {repo}: #Lb", paper_lb, db_lb))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Verify the paper's claims against the database")
    parser.add_argument("--db", default=LB_PATH, help="Path to SQLite database")
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    cur = con.cursor()

    print("=" * 60)
    print("  ReproBreak: paper claims vs. shipped database")
    print("=" * 60)

    print("Dataset scale")
    ok = report(scale_rows(cur))
    print("Table 2 (locator changes per framework)")
    ok &= report(table2_rows(cur))
    print("Table 1 (reproduced projects)")
    ok &= report(table1_rows(cur))
    con.close()

    print("Not checkable from the database (see README):")
    print("  - Table 1 #Lc_valid (580) and #Lnb (131): require re-running Phase 2")
    print("  - Table 2 project denominators (189/154/16): Phase-1 detection, not persisted")

    print("=" * 60)
    if ok:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED (see [FAIL] lines above)")
        sys.exit(1)


if __name__ == "__main__":
    main()
