# Contributing to AutoGaitA

Thank you for your interest in AutoGaitA! We are a small team at Forschungszentrum
Jülich and the University of Cologne, and we genuinely welcome outside
contributions — whether that is a bug report, a documentation fix, support for a
new tracking format, or a new kinematic feature.

This document explains how to get involved and what we expect from a
contribution, so that your work can be merged quickly and with as little
back-and-forth as possible.

- **Questions and ideas:** open an [issue](https://github.com/mahan-hosseini/AutoGaitA/issues)
  or email us at [autogaita@fz-juelich.de](mailto:autogaita@fz-juelich.de).
- **Code of conduct:** we expect all interactions in issues, pull requests and
  email to be respectful and constructive.

## Ways to contribute

You do not need to write code to help us.

- **Report a bug.** Please include your OS, Python version, AutoGaitA version, the toolbox you were running (DLC,
  SLEAP, Universal 3D or Group), and the full error traceback and/or screenshots.
- **Request a feature.** Tell us about the scientific question behind the request. Knowing the species,
  behaviour and tracking method you work with helps us design a solution that generalises.
- **Improve the documentation.** If something in the
  [documentation](https://docs.google.com/document/d/1iQxSwqBW3VdIXHm-AtV4TGlgpJPDldogVx6qzscsGxA/edit?usp=sharing),
  the README or a tutorial video was confusing, tell us — this is one of the most
  valuable contributions we receive.
- **Share your use case.** If you used AutoGaitA on a new species, behaviour or
  disease model, we would love to hear about it and to link your publication in
  our reference list.
- **Contribute code.** See below.

## Before you start writing code

**Please open an issue before starting work on a larger change**, or comment on
an existing one to say you are picking it up. This is the single most helpful
thing you can do: it lets us tell you early whether a feature fits AutoGaitA's
scope, whether someone is already working on it, and which module is the right
place for it. It avoids the disappointing situation of a well-written pull
request that we cannot merge because it conflicts with planned changes.

For small, self-contained fixes (typos, an obvious bug, a clearer error message)
feel free to open a pull request directly.

## Development setup

AutoGaitA requires Python >= 3.10.

```bash
git clone https://github.com/mahan-hosseini/AutoGaitA.git
cd AutoGaitA
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

The `dev` extra installs `pytest` and `hypothesis`. To run the GUI from your
working copy:

```bash
autogaita
```

## Repository layout

Knowing where things live will save you time:

| Path | Contents |
| --- | --- |
| `autogaita/common2D/` | Shared pipeline for 2D GaitAs (DLC and SLEAP) (preparation, cycle extraction, analysis, plots) |
| `autogaita/dlc/`, `autogaita/sleap/` | Thin entry points wrapping the 2D pipeline |
| `autogaita/universal3D/` | 3D pipeline |
| `autogaita/group/` | Group-level comparison, statistics and PCA |
| `autogaita/gui/` | `customtkinter` GUIs |
| `autogaita/resources/` | Shared constants, utilities and assets |
| `autogaita/batchrun_scripts/` | Example scripts for running AutoGaitA without the GUI |
| `tests/` | Unit and approval tests plus their test data |

The first-level pipelines follow a numbered order that mirrors the workflow —
`1_preparation` → `2_sc_extraction` → `3_analysis` → `4_plots`. Please keep new
code in the stage where it belongs, and put anything shared between the 2D and
3D pipelines in `autogaita/resources/utils.py`. The group pipeline follows a similar 
sequential procedure in main.

## What we expect from a pull request

1. **Branch from `main`** and keep one logical change per pull request. Small,
   focused pull requests get reviewed much faster than large mixed ones.
2. **Tests pass.** Run the full suite locally before pushing:

   ```bash
   pytest
   ```

   To skip the long-running approval tests while iterating:

   ```bash
   pytest -m "not slow"
   ```

3. **New behaviour comes with a test.** Add a unit test next to the existing ones
   in `tests/`. For bug fixes, a test that fails before your fix and passes after
   it is ideal. If your change alters numerical output, our approval tests
   (`test_dlc_approval.py`, `test_universal3D_approval.py`,
   `test_group_approval.py`) will flag it — please explain in the pull request
   why the new values are correct.
4. **Code is formatted with [black](https://black.readthedocs.io/).** Our CI
   enforces this:

   ```bash
   black .
   ```

5. **Describe the change.** In the pull request, tell us what problem it solves,
   how you tested it, and — if it affects analysis output — what users should
   expect to see differently.
6. **Configuration changes need a note.** AutoGaitA's cfg dictionaries are
   consumed by users' custom scripts and by AutoGaitA Group when reading
   first-level results. If you add, rename or remove a cfg key, say so
   explicitly so we can document it in the release notes.

## Continuous integration

Every push and pull request to `main` runs our GitHub Actions workflow, which
executes the test suite on Python 3.10, 3.11 and 3.12 and checks formatting with
black. Coverage is reported to Codecov, please make sure it does not drop too much. 

## Licensing and copyright

AutoGaitA is licensed under [GPL-3.0-only](LICENSE), and Forschungszentrum
Jülich GmbH holds the copyright. By submitting a pull request you agree that
your contribution is licensed under the same terms. For substantial
contributions we may ask you to confirm this in writing.

## Credit

We take credit seriously. Contributors are listed in the README, and
contributions that materially shape the toolbox are acknowledged in future publications appropriately. 
If you would like to be listed differently — or not at all — just tell us.

We are looking forward to your input and ideas 😊
