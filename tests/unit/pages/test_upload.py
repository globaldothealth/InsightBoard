from unittest.mock import patch
from InsightBoard.pages.upload import (
    update_filename,
    update_page_size,
    update_table,
    remove_quotes,
    clean_value,
    # update_edited_data,
    # error_report_message,
    # text_to_html,
    # errorlist_to_sentence,
    # errors_to_dict,
    # validate_errors,
    # validate_log,
    # ctx_trigger,
    # parse_file,
    # parse_data,
    # highlight_and_tooltip_changes,
    # update_table_style_and_validate,
    # download_csv,
    # display_confirm_dialog,
    # commit_to_database,
)


def test_update_filename():
    filename = "test.csv"
    style = {}
    msg, new_style = update_filename(filename, style)
    assert msg == f"Selected file: {filename}"
    assert new_style.get("borderStyle", None) == "solid"


def test_update_filename_empty():
    filename = ""
    style = {}
    msg, new_style = update_filename(filename, style)
    assert msg == "Select a data file"
    assert new_style.get("borderStyle", None) == "dashed"


def test_update_page_size():
    # passthrough
    for page_size in ["10", "20", "50", "100"]:
        assert page_size == update_page_size(page_size)


def test_update_table():
    row1 = {"col1": "1", "col2": "2", "col3": "3"}
    row2 = {"col1": "4", "col2": "5", "col3": "6"}
    table1 = [row1, row2]
    row3 = {"col1": "7", "col2": "8", "col3": "9"}
    row4 = {"col1": "10", "col2": "11", "col3": "12"}
    table2 = [row3, row4]
    expected_columns = [
        {
            "editable": False,
            "id": "_delete",
            "name": "_delete",
        },
        {
            "editable": False,
            "id": "Row",
            "name": "Row",
        },
        {
            "editable": True,
            "id": "col1",
            "name": "col1",
        },
        {
            "editable": True,
            "id": "col2",
            "name": "col2",
        },
        {
            "editable": True,
            "id": "col3",
            "name": "col3",
        },
    ]

    project = "project"
    options = ["table1", "table2"]
    unique_table_id = "project-table1"
    edited_datasets = [table1, table2]
    parsed_datasets = edited_datasets
    only_show_validation_errors = False
    update_existing_records = True
    remove_empty_ids_n_clicks = None
    remove_error_rows_n_clicks = None
    restore_deleted_rows_n_clicks = None
    active_cell = None
    errors = []

    # Mock clean_dataset
    def _clean_dataset(data, *args, **kwargs):
        return data  # passthrough

    # Return table1
    selected_table = "table1"
    with (
        patch("InsightBoard.pages.upload.clean_dataset") as mock_clean_dataset,
        patch("InsightBoard.pages.upload.dash.callback_context") as mock_ctx,
        patch("InsightBoard.pages.upload.ctx_trigger") as mock_ctx_trigger,
        patch("InsightBoard.utils.get_project") as mock_get_project,
    ):
        mock_clean_dataset.side_effect = _clean_dataset
        mock_ctx.triggered = []
        mock_ctx_trigger.return_value = False
        mock_get_project.database.get_primary_key.return_value = "col1"
        columns, hidden_columns, data, new_active_cell, data_stats = update_table(
            options,
            selected_table,
            unique_table_id,
            only_show_validation_errors,
            update_existing_records,
            remove_empty_ids_n_clicks,
            remove_error_rows_n_clicks,
            restore_deleted_rows_n_clicks,
            active_cell,
            project,
            edited_datasets,
            parsed_datasets,
            errors,
        )
    # Compare columns
    for col, expected_column in zip(columns, expected_columns):
        assert col.keys() == expected_column.keys()
        for k, v in col.items():
            assert v == expected_column[k]
    # Check return data matches table1
    assert data == table1

    # Return table2
    selected_table = "table2"
    with (
        patch("InsightBoard.pages.upload.clean_dataset") as mock_clean_dataset,
        patch("InsightBoard.pages.upload.dash.callback_context") as mock_ctx,
        patch("InsightBoard.pages.upload.ctx_trigger") as mock_ctx_trigger,
        patch("InsightBoard.utils.get_project") as mock_get_project,
    ):
        mock_clean_dataset.side_effect = _clean_dataset
        mock_ctx.triggered = []
        mock_ctx_trigger.return_value = False
        mock_get_project.database.get_primary_key.return_value = "col1"
        columns, hidden_columns, data, new_active_cell, data_stats = update_table(
            options,
            selected_table,
            unique_table_id,
            only_show_validation_errors,
            update_existing_records,
            remove_empty_ids_n_clicks,
            remove_error_rows_n_clicks,
            restore_deleted_rows_n_clicks,
            active_cell,
            project,
            edited_datasets,
            parsed_datasets,
            errors,
        )
    # Compare columns
    for col, expected_column in zip(columns, expected_columns):
        assert col.keys() == expected_column.keys()
        for k, v in col.items():
            assert v == expected_column[k]
    # Check return data matches table2
    assert data == table2


def test_remove_quotes():
    assert remove_quotes("'1'") == "1"
    assert remove_quotes('"1"') == "1"
    assert remove_quotes("1") == "1"
    assert remove_quotes("") == ""
    assert remove_quotes(None) is None


def test_clean_value():
    number_type = ["k", {"k": {"type": "number"}}]
    integer_type = ["k", {"k": {"type": "integer"}}]
    array_type = ["k", {"k": {"type": "array"}}]
    number_or_null_type = ["k", {"k": {"type": ["number", "null"]}}]
    bool_or_null_type = ["k", {"k": {"type": ["boolean", "null"]}}]
    assert clean_value("1") == "1"
    assert clean_value("1", *number_type) == 1
    assert clean_value("1", *integer_type) == 1
    assert clean_value("1.0") == "1.0"
    assert clean_value("1", *number_type) == 1.0
    assert clean_value("1.1.1") == "1.1.1"
    assert clean_value("[1, 2, 3]", *array_type) == [1, 2, 3]
    assert clean_value("[1]") == "[1]"
    assert clean_value("[1]", *array_type) == [1]
    assert clean_value("[a]") == "[a]"
    assert clean_value("[a]", *array_type) == ["a"]
    assert clean_value("[a, b, c]", *array_type) == ["a", "b", "c"]
    assert clean_value('["a", "b", "c"]', *array_type) == ["a", "b", "c"]
    assert clean_value("'a', 'b', 'c'", *array_type) == ["a", "b", "c"]
    assert clean_value("a, b, c", *array_type) == ["a", "b", "c"]
    assert clean_value("0", *number_or_null_type) == 0
    assert clean_value(0, *number_or_null_type) == 0
    assert clean_value("False", *bool_or_null_type) is False
    assert clean_value(False, *bool_or_null_type) is False


def test_update_edited_data():
    # update_edited_data(
    #     parsed_data, edited_table_data, tables, selected_table, datasets
    # )
    ...


def test_error_report_message():
    # error_report_message(errors: []) -> str:
    ...


def test_text_to_html():
    # text_to_html(text: str) -> html.Div:
    ...


def test_errorlist_to_sentence():
    # errorlist_to_sentence(errorlist: []) -> str:
    ...


def test_errors_to_dict():
    # errors_to_dict(errors):
    ...


def test_validate_errors():
    # validate_errors(
    #     parsed_dbs_dict,
    #     parsed_dbs,
    #     selected_table,
    #     project,
    # )
    ...


def test_validate_log():
    # validate_log(
    #     errors,
    #     warns,
    #     parsed_dbs_dict,
    #     parsed_dbs,
    #     selected_table,
    #     show_full_validation_log,
    #     page_current,
    #     page_size,
    #     project,
    # ):
    ...


def test_ctx_trigger():
    # ctx_trigger(ctx, event):
    ...


def test_parse_file():
    # parse_file(
    #     parse_n_clicks,
    #     update_n_clicks,
    #     project,
    #     contents,
    #     filename,
    #     selected_parser,
    #     edited_data_store,
    #     tables_list,
    #     selected_table,
    # ):
    ...


def test_parse_data():
    # parse_data(project, contents, filename, selected_parser):
    ...


def test_highlight_and_tooltip_changes():
    # highlight_and_tooltip_changes(
    #     original_data, data, page_current, page_size, validation_errors
    # )
    ...


def test_update_table_style_and_validate():
    # update_table_style_and_validate(
    #     data,
    #     page_current,
    #     page_size,
    #     validation_errors,
    #     original_data,
    #     tables,
    #     selected_table,
    # )
    ...


def test_download_csv():
    # download_csv(n_clicks, data)
    ...


def test_display_confirm_dialog():
    # display_confirm_dialog(n_clicks, table_names):
    ...


def test_commit_to_database():
    # commit_to_database(submit_n_clicks, project, table_names, datasets):
    ...
