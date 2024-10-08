import time
import pytest
from pathlib import Path
from utils import (
    driver,
    page_upload,
    chromedriver_present,
)


@pytest.mark.skipif(not chromedriver_present, reason="chromedriver not present")
def test_insightboard(driver):
    upload = page_upload(driver)
    upload.clear_data()
    upload.select_parser("adtl-source1")
    data_file = str(
        Path(__file__).parent
        / "InsightBoard"
        / "projects"
        / "sample_project"
        / "data"
        / "sample_data_source1.csv"
    )
    upload.select_data_file(data_file)
    upload.parse()
    time.sleep(1)
    assert len(upload.datatable_rows()) == 20
    # Only show validation errors: Check that the validated rows are hidden
    upload.toggle_only_show_validation_errors()
    time.sleep(1)
    assert len(upload.datatable_rows()) == 10
    # Revert to showing all rows
    upload.toggle_only_show_validation_errors()
    time.sleep(1)
    assert len(upload.datatable_rows()) == 20
