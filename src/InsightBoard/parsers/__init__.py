import os
import subprocess
import tomllib
import pandas as pd
from tempfile import NamedTemporaryFile


def adtl(df: pd.DataFrame, specification: str) -> pd.DataFrame:
    # Write pandas dataframe to temporary csv file
    input_csv = NamedTemporaryFile(delete=False)
    df.to_csv(input_csv.name, index=False)

    # Read specification file to determine output files
    with open(specification, "rb") as file:
        spec = tomllib.load(file)
    tables = spec.get("adtl", {}).get("tables", {}).keys()

    # Use ADTL to parse the dataset
    result = subprocess.run(["adtl", specification, input_csv.name])

    # Remove temporary csv file
    os.unlink(input_csv.name)

    return {
        "stdout": result.stdout,
    }
