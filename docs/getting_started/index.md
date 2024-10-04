# Getting started

## Installation

InsightBoard is a Python application that runs through your web browser. You can install InsightBoard using pip:

```bash
pip install InsightBoard
```

````{note}
You will also need to install `ADTL` (Another Data Transform Language) to make full use of the parsers, including those supplied with the `sample_project`:
```bash
pip install "adtl[parquet] @ git+https://github.com/globaldothealth/adtl"
```
````

Note that it is usually recommended to install into a virtual environment. We recommend using [uv](https://github.com/astral-sh/uv) to manage the virtual environment. To create and active a virtual environment for InsightBoard using `uv` run the following commands:

```bash
uv sync
. .venv/bin/activate
```

To launch the dashboard you can now type `InsightBoard` from the command line. The dashboard should appear in your default web browser. By default the dashboard will be available at http://localhost:8050/.

## Projects

By default InsightBoard will create a folder called `InsightBoard/projects` in your home directory. This is where all your projects will be stored (you can change this location in the Settings panel of the dashboard).

We recommend that you store each project in a separate (version controlled) git repository within the projects folder. This will allow you to easily share your projects with others and keep track of any changes. _You don't have to store any data in the repository if you want to keep that private, but it is still recommended for the parsers and reports._

For example, to access an existing project (here we provide a sample project called `sample_project`) in the `InsightBoard/projects` folder, you can run the following commands from the command line:

```bash
cd ~/InsightBoard/projects
git clone git@github.com:globaldothealth/InsightBoard-SampleProject.git sample_project
```

Details of how to create a new project are provided in the [projects](../projects/index.md) section.


## Development

To launch the dashboard in development mode, follow the [Installation](../getting_started/index) instructions but instead launch with `python -m InsightBoard`.
