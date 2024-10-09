import time
import pytest
from pathlib import Path
from utils import (
    driver,
    page_upload,
    chromedriver_present,
)


def check_DataTable_row_count(upload, count):
    timeout = 30
    start_time = time.time()
    while time.time() - start_time < timeout:
        rows = upload.datatable_rows()
        if len(rows) == count:
            break
        time.sleep(1)
    else:
        assert False, f"Expected {count} rows in DataTable, but got {len(rows)}."


def save_screenshot(driver, name="screenshot"):
    screenshot_path = Path(f"{name}.png")
    driver.save_screenshot(screenshot_path)
    return str(screenshot_path)


@pytest.mark.skipif(not chromedriver_present, reason="chromedriver not present")
def test_insightboard(driver):
    upload = page_upload(driver)
    upload.clear_data()
    try:
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
        check_DataTable_row_count(upload, 20)
        # Only show validation errors: Check that the validated rows are hidden
        upload.toggle_only_show_validation_errors()
        time.sleep(1)
        check_DataTable_row_count(upload, 10)
        # Revert to showing all rows
        upload.toggle_only_show_validation_errors()
        time.sleep(1)
        check_DataTable_row_count(upload, 20)
    except Exception as e:
        screenshot_path = save_screenshot(driver)
        raise Exception(f"Screenshot saved to: {screenshot_path}") from e
