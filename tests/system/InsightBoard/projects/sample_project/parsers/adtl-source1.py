from tempfile import NamedTemporaryFile
import pandas as pd
from pathlib import Path
import adtl
from InsightBoard.parsers import parse_adtl

SPECIFICATION_FILE = Path("adtl") / "source1.toml"
TABLE_NAME = "linelist"


def parse(df: pd.DataFrame) -> list[dict]:
    spec_file = Path(__file__).parent / SPECIFICATION_FILE
    return parse_adtl(df, spec_file, [TABLE_NAME])


def test_parse():
    print("Test: Parse")
    data_file = Path(__file__).parent.parent / "data" / "sample_data_source1.csv"
    orig_df = pd.read_csv(data_file)
    rtn = parse(orig_df)
    df = rtn[0]["data"]
    assert isinstance(df, pd.DataFrame)
    print("Test: Parse - Passed")


if __name__ == "__main__":
    test_parse()
