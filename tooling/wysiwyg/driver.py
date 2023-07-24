
__all__ = ["Driver", "BASE_URL"]

from selenium import webdriver
from typing import Any, Final

BASE_URL: Final[str] = "localhost:8000"


class Driver:
    def __init__(self) -> None:
        self.driver = webdriver.Firefox()
        self.page = BASE_URL
        self.driver.get(self.page)

    def refresh(self, url: str | None = None) -> None:
        scroll_height = None
        if url is None or self.page == url:
            scroll_height = self.page_y_offset()
        else:
            self.page = url
        self.driver.get(self.page)
        self.driver.refresh()
        if scroll_height is not None:
            self.scroll_to(scroll_height)

    def page_y_offset(self) -> Any:  # noqa: ANN401
        return self.driver.execute_script("return window.pageYOffset")

    def scroll_to(self, scroll_height: Any) -> None:  # noqa: ANN401
        self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")
