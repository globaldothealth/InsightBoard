# InsightBoard

[![Unit and integration tests](https://github.com/globaldothealth/InsightBoard/actions/workflows/ci.yaml/badge.svg)](https://github.com/globaldothealth/InsightBoard/actions/workflows/ci.yaml) [![Documentation Status](https://readthedocs.org/projects/insightboard/badge/?version=latest)](https://insightboard.readthedocs.io/en/latest/?badge=latest)

A dashboard to upload and manage data and generate reports.

Documentation: [ReadTheDocs](https://insightboard.readthedocs.io/en/latest)

## Installation

Install **Insight**Board using your favourite package manager. For `pip` this would be:
```bash
pip install InsightBoard
```

You will also want to install ADTL (Another Data Transform Language) to make full use of the parsers, including those supplied with the sample project:
```bash
pip install "adtl[parquet] @ git+https://github.com/globaldothealth/adtl"
```

To launch the dashboard, simply type `InsightBoard` from the command line. The dashboard should appear in your default web browser. By default the dashboard will be available at http://localhost:8050/.

## Getting started

By default InsightBoard will create a folder called `InsightBoard/projects` in your home directory. This is where all your projects will be stored (you can change this location in the Settings panel of the dashboard).

We recommend that you store each project in a separate (version controlled) git repository within the projects folder. This will allow you to easily share your projects with others and keep track of any changes.

For example, to set up an existing project called `my_project` in the `InsightBoard/projects` folder, you can run the following commands from the command line:

```bash
cd ~/InsightBoard/projects
git clone <url> my_project
```

Details of how to create a new project are provided in the accompanying [documentation](https://insightboard.readthedocs.io/en/latest/).


## Development

If you have cloned the repository, it is recommended to install into a virtual environment. We use [uv](https://docs.astral.sh/uv/) to manage virtual environments. First, [install `uv`](https://docs.astral.sh/uv/getting-started/installation/), then activate the virtual environment:

```bash
uv sync
. .venv/bin/activate
```

To launch the dashboard in development mode run `python -m InsightBoard`.
