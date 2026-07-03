# Extending ReproBreak

The artifact has three extension points: adding repositories to the dataset, supporting new frameworks or locator APIs, and creating reproduction environments for more projects.

## 1. Adding repositories (Phase 1)

Mine any GitHub repository directly:

```bash
uv run create_dataset.py owner/repo [owner/repo2 ...]
```

Or add it to `REPO_LIST` in `config.py` and run `uv run create_dataset.py`. The pipeline clones the repository, detects its GUI test files, walks the commit history of each test file, and extracts locator changes from the diffs into a new SQLite database under `output/`. To append to an existing database instead, set `START_WITH_CLEAN_DB = False` in `config.py`.

Test files are detected in `helpers.py`:

- `detect_language_from_extension()` supports Java, JavaScript, TypeScript, and Python.
- Filename rules come first, for example `*.spec.ts`, `*Test.java`, and `test_*.py`. Files that do not match them are checked by content.
- `detect_framework_from_text()` requires both a framework indicator, such as an import or a `cy.` call, and a test indicator, such as `it(` or `@Test`. It returns `cypress`, `playwright`, or `puppeteer`.

## 2. Supporting new frameworks or locator APIs

Locator extraction is regex based. To cover another locator API or a new framework:

1. **Add extraction patterns** to the `patterns` list in `helpers.py`. Each pattern must match the full locator call and capture its argument, following the existing shape:

   ```python
   re.compile(r"page\.getByLabel\((.+?)\)(?=[;.\s]|$)"),
   ```

2. **Add framework detection** in `detect_framework_from_text()` in `helpers.py`. That is one import or usage regex per language.

3. If the new framework's test runner will be used in reproductions, **extend `parse_test_result()`** in `create_reproducible_dataset.py`. It decides whether tests actually started by looking for runner-specific output markers. The current markers are `Running N tests using N workers` for Playwright and `Run Starting` for Cypress. Add a marker for the new runner.

How the mining decides what a locator change is: `get_locator_break_for_commit_in_file()` in `helpers.py` records a change when a removed line containing a locator is followed by an added line containing a different locator within the same diff hunk. Changes that only differ in assertions are discarded, see `strip_assertions()` in `analyze_locator_changes.py`. Locator calls spanning multiple lines are not captured. The paper documents this undercount in Section 2.2.

## 3. Creating a reproduction environment (Phase 2)

Reproduction environments turn mined locator changes into validated locator breaks. Each environment consists of two files placed at `data/reproduction_files/repos/<repo-name>/`, where `<repo-name>` is the part after the `/` of `owner/repo`.

### 3.1 The Dockerfile contract

- The build context is `data/reproduction_files/repos/<repo-name>/`. It contains the project clone in `./<repo-name>`, checked out at the commit under evaluation, and your `run_tests.sh`.
- The image must copy the application to `/app` and the runner to `/run_tests.sh`. It must install everything needed to build and run the application and its GUI tests.

### 3.2 The run_tests.sh contract

- It receives the test file to run as its first argument, as an absolute path inside the container, for example `/app/test/cypress/e2e/example06.cy.ts`. Without arguments it should run the whole suite.
- It must start the application, wait until the application is ready, and then run the tests.
- It must exit non-zero when tests fail and zero when they pass. The exit code is how `parse_test_result()` distinguishes pass from fail.
- Its output must include the framework's start marker, see Section 2 above. The standard Cypress and Playwright runners print these markers.

### 3.3 Worked example

The angular-slickgrid environment shipped in the `reproduce_files` table:

```dockerfile
FROM cypress/browsers

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ./angular-slickgrid .
COPY ./run_tests.sh /run_tests.sh

RUN yarn install
RUN cd test/cypress && yarn install && npx cypress install
RUN yarn build
RUN yarn build:demo
```

```sh
#!/bin/sh
yarn serve:demo &
npx wait-on http://localhost:4300 --timeout 120000
cd /app/test/cypress
if [ -n "$1" ]; then
  yarn cypress:ci --spec "$1"
else
  yarn cypress:ci
fi
```

### 3.4 Running and persisting

```bash
uv run create_reproducible_dataset.py owner/repo   # validate the locator changes
uv run analyze_results.py repo-name <run_number>   # inspect a run
uv run save_reproduction.py owner/repo             # write confirmed breaks to the database
```

`create_reproducible_dataset.py` builds one image per commit with a locator change and runs each affected test file, with a 5-minute timeout per run. For passing files it re-runs the tests with each locator reverted to its old value. A now-failing run marks a reproducible break. Progress is tracked in `reproduction.json` and `results/<n>/results.json`, so interrupted sessions resume where they left off, and commits with errors are retried on the next run.

A single application version rarely builds across a project's whole history. Expect to refine the Dockerfile and re-run several times, as in step 2c of Figure 2 in the paper. Each round gets a new numbered results folder.
