import time
import pytest
from pathlib import Path
from utils import (  # noqa: F401 (linter does not recognise driver as a fixture)
    driver,
    page_upload,
    select_project,
    chromedriver_present,
    save_screenshot,
)


@pytest.mark.skipif(not chromedriver_present, reason="chromedriver not present")
def test_insightboard(driver):  # noqa: F811 (driver is a fixture)
    try:
        select_project(driver, "sample_project")
        upload = page_upload(driver)
        upload.clear_data()
        upload.select_parser("adtl-source1")
        data_file = (
            Path(__file__).parent
            / "InsightBoard"
            / "projects"
            / "sample_project"
            / "data"
            / "sample_data_source1.csv"
        )
        assert data_file.exists()
        upload.select_data_file(str(data_file))
        upload.parse()
        time.sleep(1)
        upload.check_DataTable_row_count(20)
        # Only show validation errors: Check that the validated rows are hidden
        upload.toggle_only_show_validation_errors()
        time.sleep(1)
        upload.check_DataTable_row_count(10)
        # Revert to showing all rows
        upload.toggle_only_show_validation_errors()
        time.sleep(1)
        upload.check_DataTable_row_count(20)
    except Exception as e:
        screenshot_path = save_screenshot(driver)
        raise Exception(f"Screenshot saved to: {screenshot_path}") from e
