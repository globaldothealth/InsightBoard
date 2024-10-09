import time
import pytest
import tomllib
import tomli_w

import InsightBoard

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chromedriver_py import binary_path


def chromedriver_present():
    try:
        Service(binary_path)
    except Exception:
        return False
    return True


@pytest.fixture
def driver():
    service = Service(binary_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=service, options=options)

    # Override default project location
    config_file = Path.home() / ".insightboard" / "config.toml"
    try:
        with open(config_file, "r") as f:
            config = tomllib.loads(f.read())
    except FileNotFoundError:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config = {}
    new_config = {
        "project": {"folder": str(Path(__file__).parent / "InsightBoard" / "projects")}
    }
    with open(config_file, "w") as f:
        f.write(tomli_w.dumps(new_config))

    # Launch InsightBoard and wait for server to start
    process = InsightBoard.launch_app()
    InsightBoard.wait_for_server()

    # Open the Dash app in the browser
    driver.get("http://127.0.0.1:8050")
    for _ in range(10):
        try:
            driver.find_element(By.TAG_NAME, "h1")
            break
        except Exception:
            time.sleep(1)

    # Stat with the sample project selected
    select_project(driver, "sample_project")

    yield driver

    # Restore the InsightBoard config file and close chromedriver / Dash app
    driver.quit()
    if config:
        with open(config_file, "w") as f:
            f.write(tomli_w.dumps(config))
    process.kill()
    process.wait()


def select_project(driver, project_name):
    dropdown_select(driver, "project-dropdown", project_name)


def page_upload(driver):
    upload_link = driver.find_element(
        By.XPATH, '//a[@class="nav-link" and @href="/upload"]'
    )
    upload_link.click()
    # assert that the upload page is loaded
    time.sleep(1)
    assert driver.find_element(By.TAG_NAME, "h1").text == "Upload data"
    return PageUpload(driver)


def dropdown_select(driver, dropdown_id, option):
    dropdown = driver.find_element(By.ID, dropdown_id)
    dropdown.click()
    option_to_select = dropdown.find_element(By.XPATH, f'//div[text()="{option}"]')
    option_to_select.click()
    dropdown_value = dropdown.find_element(By.CLASS_NAME, "Select-value-label")
    assert dropdown_value.text == option


class PageUpload:
    def __init__(self, driver):
        self.driver = driver
        self.project_folder = (
            Path(__file__).parent / "InsightBoard" / "projects" / "sample_project"
        )

    def clear_data(self):
        data_folder = self.project_folder / "data"
        for file in data_folder.glob("*.parquet"):
            file.unlink()

    def select_parser(self, parser_name):
        dropdown_select(self.driver, "parser-dropdown", parser_name)

    def select_data_file(self, file_path):
        input_box = self.driver.find_element(By.XPATH, '//input[@type="file"]')
        input_box.send_keys(file_path)

    def parse(self):
        parse_button = self.driver.find_element(By.ID, "parse-button")
        parse_button.click()

    def datatable_rows(self):
        table_rows = self.driver.find_elements(
            By.XPATH, "//div[@id='editable-table']//table//tr"
        )
        table_rows = table_rows[
            len(table_rows) // 2 + 1 :
        ]  # skip duplicates and header
        return table_rows

    def toggle_only_show_validation_errors(self, new_state=None):
        checkbox = self.driver.find_element(
            By.XPATH,
            "//label[text()='Only show validation errors']/preceding::input[1]",
        )
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", checkbox
        )
        time.sleep(1)
        checkbox = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//label[text()='Only show validation errors']/preceding::input[1]",
                )
            )
        )
        checkbox.click()
