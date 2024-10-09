import nox

PYTHON_VERSIONS = ["3.11", "3.12"]


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def unit_tests(session):
    """Unit tests (with coverage)"""
    session.env.update({"UV_PROJECT_ENVIRONMENT": session.virtualenv.location})
    session.run(
        "uv",
        "sync",
        "--all-extras",
    )
    session.run(
        "uv",
        "run",
        "pytest",
        "--cov=InsightBoard",
        "--cov-report=html",
        "tests/unit",
    )


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
def system_tests(session):
    """System tests"""
    session.env.update({"UV_PROJECT_ENVIRONMENT": session.virtualenv.location})
    session.run(
        "uv",
        "sync",
        "--all-extras",
    )
    session.run(
        "uv",
        "pip",
        "install",
        "adtl[parquet] @ git+https://github.com/globaldothealth/adtl",
    )
    session.run(
        "uv",
        "run",
        "pytest",
        "tests/system",
    )
