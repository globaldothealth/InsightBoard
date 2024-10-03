# Parsers

Parsers are Python files that define functions to ingest data from various formats. They should be saved in the `parsers` folder of the project.

The parser accepts a pandas dataframe as input to a `parse` function. The `parse` function should return a list of dictionaries specifying the table name and parsed pandas dataframe. Since the parser returns a list, it can return multiple tables.

Since the parser is written in Python, the function can make use of other Python packages. In particular we recommend using the `ADTL` package for parsing the data. However, befor we explore `ADTL`, let's first look at a simple example of a parser that handles pandas dataframes directly:

```python
import pandas as pd

def parse(data: pd.DataFrame) -> list[dict]:

    # For example, rename columns ...
    data = data.rename(
        columns={
            "DateOfEvent": "date",
            "place": "country",
        }
    )

    # ... substitute values in the 'country' column ...
    data["country"] = data["country"].replace(
        {
            "USA": "United States",
            "UK": "United Kingdom",
        }
    )

    # ... drop all columns except 'date', 'country', and 'value'
    data = data[["date", "country", "value"]]

    return [
        {
            "database": "linelist",     # Target table = "linelist"
            "data": data,               # Parsed data
        },
    ]
```

````{note}
A note on testing. Since the parser is called on the `parse` function entrypoint, it can be useful to test the parser outside of InsightBoard. This can be done by running the parser as a Python script with a sample dataset. For example, add the following to the parser script:

```python
if __name__ == "__main__":
    # Sample data
    data = pd.DataFrame(
        {
            "DateOfEvent": ["2021-01-01", "2021-01-02"],
            "place": ["USA", "UK"],
            "value": [100, 200],
        }
    )
    # Parse the sample data using the parse() function
    tables = parse(data)
    # Validate that the output is as expected
    df = tables[0]["data"]
    assert isinstance(df, pd.DataFrame)
    assert tables[0]["database"] == "linelist"
    assert df.columns.tolist() == ["date", "country", "value"]
    assert df["country"].tolist() == ["United States", "United Kingdom"]
    # Print the parsed data
    print(tables)
```
````

## ADTL

[ADTL](https://github.com/globaldothealth/adtl) (Another Data Transformation Language) is a Python package that provides a simple and powerful way to parse data. It is designed to be easy to use and understand, and can be used to parse data from various formats. `ADTL` makes use of the `json` schema we have already defined, along with a specification file which defines the parsing rules.

An example of a specification file is shown below, where full details of the `ADTL` syntax can be found in the [ADTL documentation](https://github.com/globaldothealth/adtl):
```toml
[adtl]
  name = "source1"

  [adtl.tables]
    linelist = { kind = "oneToOne", schema = "../../schemas/linelist.schema.json" }

[linelist]
  [linelist.country]
    field = "DateOfEvent"
    country = "place"
    
    [linelist.country.values]
      "US" = "United States"
      "UK" = "United Kingdom"
```

InsightBoard provides helper functions to run the `ADTL` parser. Specifically, the `parse_adtl` function can be used to parse data and return directly from the `parse` function, for example:
```python
import pandas as pd
from pathlib import Path
from InsightBoard.parsers import parse_adtl

def parse(data: pd.DataFrame) -> list[dict]:
    spec_file = Path(__file__).parent / "adtl" / "specification.toml"
    table_list = ["linelist"]
    return parse_adtl(data, spec_file, table_list)
```

This will parse the data using the `ADTL` specification file located in `adtl/specification.toml` (path relative to the parser file) and return the parsed data as a list of dictionaries.
