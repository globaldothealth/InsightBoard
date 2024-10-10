# InsightBoard

[![Unit and integration tests](https://github.com/globaldothealth/InsightBoard/actions/workflows/ci.yaml/badge.svg)](https://github.com/globaldothealth/InsightBoard/actions/workflows/ci.yaml) [![Documentation Status](https://readthedocs.org/projects/insightboard/badge/?version=latest)](https://insightboard.readthedocs.io/en/latest/?badge=latest)

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/) [![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/) [![Python 3.13](https://img.shields.io/badge/python-3.13-red.svg)](https://www.python.org/downloads/release/python-3130/)

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

See the [development](dev) pages for more information.
