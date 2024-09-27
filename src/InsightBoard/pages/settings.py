import dash
from dash import html

# Register the page
dash.register_page(__name__, path="/settings")


# Layout for the Data Page
def layout():
    return html.Div(
        [
            html.H1("Settings"),
            html.Div(["There are no editable settings available at this time."]),
        ]
    )
