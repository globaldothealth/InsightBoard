import pandas as pd


def parse(df: pd.DataFrame) -> pd.DataFrame:
    df["Age"] = df["Age"] + 100

    return df
