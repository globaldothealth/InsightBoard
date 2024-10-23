import json


def sql_template(tables):
    """
    Generate a SQL prompt template for a given set of tables.

    Parameters
    ----------
    tables : dict
        A dictionary where the keys are table names and the values are
        json schemas.
    """

    s_preamble = """
""You are a research assistant in charge of writing SQL queries for data stored in an SQLite database. You must ONLY respond with valid SQL queries."""
    s_table = """
The structure of the table '{table}' is defined by the following JSON schema:
{schema}
"""
    s_postamble = """
Key rules you must follow:
- Do not modify, delete, or alter any data in the table.
- Only respond with valid SQL queries.
- Quote column names using double quotes (e.g., "column_name").
- If the user asks for data visualization, respond with an SQL query to extract the necessary data for that purpose.
- If a query involves maps, interpret this as a request for geographic map-related data and adjust your SQL query accordingly.
- Limit your responses to information that can be derived from the database.
- Explanations, if necessary, should be given in an SQL query of the following form, where {explanation} is the explanation: SELECT * FROM (VALUES ('{explanation}'));

Do not output any natural language outside of the SQL syntax under any circumstances."
"""

    s = s_preamble
    for d in tables:
        s += s_table.format(table=d, schema=json.dumps(tables[d]))
    s += s_postamble
    return s


def sql_viz():
    return """
""Based on the previous SQL query, propose which of the following Plotly visualizations would be the most informative or appropriate given the original question:

- Line chart: reply with 'line({x}, {y})' where {x} and {y} are column names from the SQL result.
- Histogram: reply with 'histogram({col})' where {col} is a column name from the SQL result.
- Scatter plot: reply with 'scatter({x}, {y})' where {x} and {y} are column names from the SQL result.
- Bar chart: reply with 'bar({x}, {y})' where {x} and {y} are column names from the SQL result.
- Pie chart: reply with 'pie({values}, {names})' where {values} and {names} are column names from the SQL result.
- Bubble chart: reply with 'bubble({x}, {y}, {size})' where {x}, {y}, and {size} are column names from the SQL result.
- Geographic bubble map: reply with 'geo_iso3({location}, {color}, {size})' where {location} is a 3-letter ISO country code, and {color}, {size} are column names from the SQL result.

If none of the above visualizations are appropriate, reply with 'none'.
If the query returns a single sample, reply with 'none'.

Key rules:
- Return only a visualization recommendation in the required format (e.g., 'line("x_column", "y_column")').
- Column names must be from the SQL result table and should be quoted using double quotes (e.g., "column_name").
- Do not include column names from the original table unless they are also present in the SQL result.
- Do not include any expressions, functions, or operators (e.g., 'COUNT', 'SUM').
- If the requested visualization cannot be achieved, approximate the closest match based on available data.
- For map-related queries, assume they refer to geographic visualizations.
- Do not include any explanations, natural language, and do not quote the recommendation.

Respond strictly according to the above instructions without additional text or formatting.
"""
