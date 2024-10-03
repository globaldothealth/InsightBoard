import adtl as adtl_parser
import subprocess
import pandas as pd
from tempfile import NamedTemporaryFile


def adtl(df: pd.DataFrame, specification: str, *cl_args) -> dict:
    """Helper function for adtl parser.

    Params:
        df: Pandas dataframe
        specification: Path to ADTL specification file
        *cl_args: List of additional command-line arguments to pass to ADTL
    """
    # Write pandas dataframe to temp file, then run adtl
    with NamedTemporaryFile(suffix=".csv") as input_csv:
        df.to_csv(input_csv.name, index=False)
        result = subprocess.run(["adtl", specification, input_csv.name, *cl_args])

    return {
        "stdout": result.stdout,
    }


def parse_adtl(df: pd.DataFrame, spec_file, table_names) -> list[dict]:
    if isinstance(table_names, str):
        table_names = [table_names]

    parser = adtl_parser.Parser(spec_file)

    # Write the dataframe to a temporary file and load it into ADTL
    with NamedTemporaryFile(suffix=".csv") as source_temp_file:
        df.to_csv(source_temp_file.name)
        parsed = parser.parse(source_temp_file.name)

    # Write the parsed data to a temporary file and load it into a pandas dataframe
    dfs = []
    for table_name in table_names:
        with NamedTemporaryFile(suffix=".csv") as parsed_temp_file:
            parsed.write_csv(table_name, parsed_temp_file.name)
            df = pd.read_csv(parsed_temp_file.name)
            # Drop ADTL-specific columns
            df.drop(columns=["adtl_valid", "adtl_error"], inplace=True)
            # Append the dataframe to the list
            dfs.append(df)

    return [
        {
            "database": table_name,
            "data": df,
        }
        for table_name, df in zip(table_names, dfs)
    ]
