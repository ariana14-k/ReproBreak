# Status

We apply for the **Artifacts Available** and **Artifacts Reusable** badges.

## Artifacts Available

The complete artifact is archived on Zenodo and released under the [MIT license](LICENSE). The Zenodo record is referenced in the artifact submission. A development mirror is maintained at <https://github.com/rub-sq/ReproBreak>.

## Artifacts Reusable

- The artifact is functional and verifiable with one command each: `smoke_test.py` checks the setup, `verify_claims.py` recomputes the paper's numbers from the database, and `reproduce.py` re-executes any of the 449 locator breaks. A reduced and a full validation scope are provided (README, Section 2).
- Claims the artifact cannot support directly are listed with reasons and re-run instructions (README, Section 2.2).
- The documentation covers the full dataset schema, provenance, ethics, and storage (README, Section 3), and the hardware and software requirements ([REQUIREMENTS.md](REQUIREMENTS.md)).
- The environment is reproducible: dependencies are pinned in `uv.lock`, the reproduction environments are Docker images whose build files ship inside the dataset, and the scripts themselves can run in a container ([Dockerfile.artifact](Dockerfile.artifact)).
- Reuse is documented: the paper's four application scenarios map to concrete entry points (README, Section 4), and [EXTENDING.md](EXTENDING.md) explains how to add repositories, frameworks, and reproduction environments.
