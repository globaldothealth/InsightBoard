from dash import html


DATASETS = ["linelist", "some_random_dataset_that_does_not_exist"]


def generate_report(linelist):
    # Return a full Dash layout
    return html.Div(
        [
            html.H1("This report should fail to load!"),
        ]
    )
