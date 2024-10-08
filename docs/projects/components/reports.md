# Reports

Reports are Python files that return a [Dash](https://dash.plotly.com/) container. Report scripts need to request tables from the InsightBoard via a `DATASETS` list, which are then provided to a `generate_report` function. The function should return a Dash object that contains the report.

For example:
```python
import pandas as pd
import plotly.express as px
from dash import html, dcc

DATASETS = ["linelist"]


def generate_report(linelist: pd.DataFrame):
    # Create a simple line chart
    fig = px.line(linelist, x="date", y="value", color="country")

    return html.Div([
        html.H1("Sample Report"),
        html.P("A sample report to demonstrate the capabilities of InsightBoard."),
        dcc.Graph(figure=fig),
    ])
```

````{note}

As with the parser, it is useful to test the report outside of InsightBoard. This can be done by running the report as a Python script with a sample dataset. For example, add the following to the report script:

```python
if __name__ == "__main__":
    # This is for testing purposes only
    data = pd.DataFrame({
        "date": ["2021-01-01", "2021-01-02"],
        "country": ["United States", "United Kingdom"],
        "value": [100, 200],
    })
    report = generate_report(data)
    print(report)
```
````

## Returning web pages

Since reports are generated by Python scripts, they can use a variety of Python libraries to create the report. It may be that such a tool produces an HTML file which you would like to display. Luckily this is very easy to do with Dash. In-fact, there are several options, but one of the simplest and most powerful is to render the HTML in an `iframe`. This can be achieved with the following code:

```python
from dash import html

DATASETS = ["linelist"]

def generate_report(linelist: pd.DataFrame):

    # some function to generate an HTML report
    report_html = generate_report_html(linelist)

    return html.Div(
        html.Iframe(
            srcDoc=report_html,
            style={"width": "100%", "height": "650px"},
        ),
    )
```
