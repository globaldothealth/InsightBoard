# InsightBoard

[![Unit and integration tests](https://github.com/globaldothealth/InsightBoard/actions/workflows/ci.yaml/badge.svg)](https://github.com/globaldothealth/InsightBoard/actions/workflows/ci.yaml) [![Documentation Status](https://readthedocs.org/projects/insightboard/badge/?version=latest)](https://insightboard.readthedocs.io/en/latest/?badge=latest)

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/) [![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/) [![Python 3.13](https://img.shields.io/badge/python-3.13-red.svg)](https://www.python.org/downloads/release/python-3130/)

A dashboard to upload and manage data and generate reports.

Documentation: [ReadTheDocs](https://insightboard.readthedocs.io/en/latest)

## Installation

First, ensure you have a compatible version of [Python 3](https://www.python.org/downloads/) installed on your computer, then install **Insight**Board using your favourite package manager. Modern Python distributions come bundled with `pip`, so this would be:
```bash
pip3 install InsightBoard
```

You will also want to install ADTL (Another Data Transform Language) to make full use of the parsers, including those supplied with the sample project:
```bash
pip3 install "adtl[parquet] @ git+https://github.com/globaldothealth/adtl"
```

To launch the dashboard, simply type `InsightBoard` from the command line. The dashboard should open in your default web browser (http://localhost:8050/). If the command is not found, you can also launch the dashboard by typing `python3 -m InsightBoard`.

### Upgrading

To upgrade to the latest version of InsightBoard, run:
```bash
pip3 install --upgrade InsightBoard
```

## Getting started

By default InsightBoard will create a folder called `InsightBoard/projects` in your home directory. This is where all your projects will be stored (you can change this location in the Settings panel of the dashboard).

We recommend that you store each project in a separate (version controlled) git repository within the projects folder. This will allow you to easily share your projects with others and keep track of any changes.

For example, to set up the `sample_project` in the `InsightBoard/projects` folder, you can run the following commands from the command line (note that this requires you to have a working [`github`](https://github.com/) account):

```bash
cd ~/InsightBoard/projects
git clone git@github.com:globaldothealth/InsightBoard-SampleProject.git sample_project
```

If you now launch `InsightBoard` it will start with the `sample_project` available from the projects dropdown list (in the upper-left of the screen). Usage details, and instructions on how to create new projects, are provided in the accompanying [documentation](https://insightboard.readthedocs.io/en/latest/).


## Developers

See the [development](dev) pages for more information.
