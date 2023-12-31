import re
import sys
import time
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from queue import Queue
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from threading import Lock
from typing import Any, Final
from watchdog.events import FileModifiedEvent, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

BASE_URL: Final[Path] = Path("http://localhost:8000")
LOCK: Final[Lock] = Lock()

TITLE_RE: Final[re.Pattern[str]] = re.compile(r"Title: (.*)")
DATE_RE: Final[re.Pattern[str]] = re.compile(r"Date: (.*)")
SLUG_RE: Final[re.Pattern[str]] = re.compile(r"Slug: (.*)")
STATUS_RE: Final[re.Pattern[str]] = re.compile(r"Status: (.*)")


def is_draft(content: str) -> bool:
    if (status_match := STATUS_RE.search(content)) is not None:
        return status_match.group(1) != "published"
    return True


def get_date(content: str) -> date:
    post_date = DATE_RE.search(content).group(1)
    return date.fromisoformat(post_date)


def chrome_mobile_emulator() -> webdriver.Chrome:
    mobile_emulation = {
        "deviceName": "iPhone X"  # You can choose other device names too
    }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    return webdriver.Chrome(options=chrome_options)


def make_driver(name: str) -> WebDriver:
    match name:
        case "firefox":
            return webdriver.Firefox()
        case "chrome":
            return webdriver.Chrome()
        case "mobile":
            return chrome_mobile_emulator()
        case "":
            return webdriver.Firefox()
        case other:
            msg = f"driver name not recognised {other}"
            raise NotImplementedError(msg)


def page_y_offset(driver: WebDriver) -> Any:  # noqa: ANN401
    return driver.execute_script("return window.pageYOffset")


def page_scroll_to(driver: WebDriver, offset: Any) -> None:  # noqa: ANN401
    driver.execute_script(f"window.scrollTo(0, {offset});")


class Reloader:
    def __init__(self, driver: str) -> None:
        self.driver = make_driver(driver)
        self.page = str(BASE_URL)
        self.driver.get(self.page)

    def refresh(self, url: Path | None = None) -> None:
        url = self.driver.current_url if url is None else str(url)
        if self.page == url:
            offset = page_y_offset(self.driver)
            self.driver.get(self.page)
            self.driver.refresh()
            page_scroll_to(self.driver, offset)
        else:
            self.page = url
            self.driver.get(self.page)
            self.driver.refresh()

    def refresh_changed(self, changed: list[str]) -> None:
        url = None
        if len(changed) != 0:
            modified_path = Path(changed[-1])
            if modified_path.suffix.endswith("md"):
                content = open(modified_path).read()
                url = BASE_URL
                if is_draft(content):
                    url = url.joinpath("drafts/")
                else:
                    post_date = get_date(content)
                    year = post_date.strftime("%Y")
                    month = post_date.strftime("%b")
                    url = url.joinpath(year).joinpath(month)
                if (slug_match := SLUG_RE.search(content)) is not None:
                    url = url.joinpath(slug_match.group(1))
                else:
                    if (title_match := TITLE_RE.search(content)) is None:
                        print(f"no title set for: {modified_path}")
                        return None
                    url = url.joinpath(title_match.group(1).lower().replace(" ", "-"))
            elif modified_path.name == "index.html":
                url = BASE_URL
        self.refresh(url)


def drain_queue(q: Queue[str]) -> Iterator[str]:
    while not q.empty():
        yield q.get(block=False)


class OutputHandler(FileSystemEventHandler):
    def __init__(self, output_changes: Queue[int]) -> None:
        self.output_changes = output_changes

    def on_modified(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileModifiedEvent):
            with LOCK:
                self.output_changes.put(1, block=False)


class SiteHandler(FileSystemEventHandler):
    def __init__(self, content_changes: Queue[str]) -> None:
        self.content_changes = content_changes

    def on_modified(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileModifiedEvent):
            if not (path := str(event.src_path)).endswith("~"):
                with LOCK:
                    self.content_changes.put(path, block=False)


def auto_refresh(driver: str) -> None:
    site_changes = Queue()
    site_handler = SiteHandler(site_changes)
    output_changes = Queue()
    output_handler = OutputHandler(output_changes)

    observer = Observer()
    observer.schedule(site_handler, "content", recursive=True)
    observer.schedule(site_handler, "themes/simple/templates")
    observer.schedule(output_handler, "output", recursive=True)
    observer.start()

    reloader = Reloader(driver)
    try:
        while True:
            with LOCK:
                if len(list(drain_queue(output_changes))) > 0:
                    changed = list(drain_queue(site_changes))
                    reloader.refresh_changed(changed)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    auto_refresh(sys.argv[1])
