import plotly.express as px
import pandas as pd
from dash import html, dcc


def generate_report():
    # Sample data for the bar chart
    df = pd.DataFrame({"Category": ["A", "B", "C", "D"], "Values": [5, 10, 8, 6]})

    # Create a Plotly bar chart
    fig = px.bar(df, x="Category", y="Values", title="Category Distribution")

    # Return a full Dash layout with text and an image
    return html.Div(
        [
            html.H1("Report 2: Category Distribution"),
            html.P(
                "This report provides a detailed overview of category distributions."
            ),
            # Descriptive text
            html.P(
                "The bar chart below shows the distribution of values across different categories."
            ),
            # Insert the Plotly graph
            dcc.Graph(figure=fig),
            # Additional conclusions
            html.P(
                "Category A has the lowest value, while Category B has the highest."
            ),
        ]
    )
