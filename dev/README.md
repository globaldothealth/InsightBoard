# Developer guide

Please consult the [documentation](https://insightboard.readthedocs.io/en/latest) for general usage.

## Virtual environment

We use [uv](https://docs.astral.sh/uv/) to manage virtual environments. First, [install `uv`](https://docs.astral.sh/uv/getting-started/installation/), then activate the virtual environment:

```bash
uv sync --all-extras
. .venv/bin/activate
```

The package will install a script allowing the production server to be launched with `InsightBoard`. To launch the dashboard manually run `python -m InsightBoard`. To launch the dashboard in debug-mode (which uses Dash's bundled Flash server) run `python -m InsightBoard --debug`. If you wish to launch `InsightBoard` from within python, `import InsightBoard` then call `InsightBoard.main()`.

## Versioning

Use [Semantic Versioning](https://semver.org/). Version management is handled by [setuptools-scm](https://setuptools-scm.readthedocs.io/en/latest/), which extracts the current version number from the git tags.

Note that `setuptools-scm` writes to a `src/InsightBoard/version.py` file which _should not_ be checked in to git (the file is listed in `.gitignore`), but will allow packaged releases to query `InsightBoard.__version__` to get the current version number. During development this will look peculiar (e.g. `0.1.0.dev...`).

## Making a release

To create a new release, navigate to github - Releases, then select `Draft a new release`. Create a new tag in the format `vX.Y.Z` (e.g. `v0.1.0`), click `Generate release notes`, then `Publish release`. This will trigger a github action that will build the Python wheels and upload the package to PyPI. It is worth keeping an eye on this action to ensure it completes successfully, and making any necessary changes if it does not.

## Building as an application

_Experimental_

To build the application as a standalone executable, we use [PyInstaller](https://www.pyinstaller.org/). This will create a `dist/InsightBoard` folder containing the executable and all necessary dependencies. To build the application, run `./dev/build_app.sh`.
