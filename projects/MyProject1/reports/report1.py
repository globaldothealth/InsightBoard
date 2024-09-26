import plotly.express as px
import pandas as pd
from dash import html, dcc


DATASETS = ["linelist"]


def generate_report(linelist):
    # Sample data for the figure
    df = pd.DataFrame({"X": list(range(len(linelist))), "Y": linelist.Age})

    # Create a Plotly figure
    fig = px.scatter(df, x="X", y="Y", title="Sample Scatter Plot")

    # Return a full Dash layout
    return html.Div(
        [
            html.H1("Report 1: Analysis of Sample Data"),
            html.P("This report provides an analysis of the following dataset."),
            # Embed an image (can be a URL or a path to an image file)
            html.Img(
                src="https://via.placeholder.com/400",
                style={"width": "400px", "height": "auto"},
            ),
            # Insert some descriptive text
            html.P(
                "Here is a scatter plot that shows the relationship between X and Y."
            ),
            # Insert the Plotly graph
            dcc.Graph(figure=fig),
            # Conclusion or additional text
            html.P("The data reveals a positive trend between X and Y."),
        ]
    )
