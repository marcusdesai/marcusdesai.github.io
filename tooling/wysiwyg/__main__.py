import time
from collections.abc import Iterator
from pathlib import Path
from queue import Queue
from selenium import webdriver
from threading import Lock
from typing import Any, Final
from watchdog.events import FileModifiedEvent, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

BASE_URL: Final[str] = "http://localhost:8000"
LOCK: Final[Lock] = Lock()


class Driver:
    def __init__(self) -> None:
        self.driver = webdriver.Firefox()
        self.page = BASE_URL
        self.driver.get(self.page)

    def refresh(self, url: str | None = None) -> None:
        url = self.driver.current_url if url is None else url
        if self.page == url:
            scroll_height = self.page_y_offset()
            self.driver.get(self.page)
            self.driver.refresh()
            self.page_scroll_to(scroll_height)
        else:
            self.page = url
            self.driver.get(self.page)
            self.driver.refresh()

    def page_y_offset(self) -> Any:  # noqa: ANN401
        return self.driver.execute_script("return window.pageYOffset")

    def page_scroll_to(self, scroll_height: Any) -> None:  # noqa: ANN401
        self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")

    def refresh_changed(self, changed: list[str]) -> None:
        url = None
        if len(changed) != 0:
            modified_path = Path(changed[-1])
            if modified_path.suffix.endswith("md"):
                url = f"{BASE_URL}/{modified_path.stem}.html"
            if modified_path.name == "index.html":
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


def auto_refresh() -> None:
    site_changes = Queue()
    site_handler = SiteHandler(site_changes)

    output_changes = Queue()
    driver = Driver()
    observer = Observer()
    observer.schedule(site_handler, "content", recursive=True)
    observer.schedule(site_handler, "themes/simple/templates")
    observer.schedule(OutputHandler(output_changes), "output", recursive=True)
    observer.start()
    try:
        while True:
            with LOCK:
                if len(list(drain_queue(output_changes))) > 0:
                    changed = list(drain_queue(site_changes))
                    driver.refresh_changed(changed)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    auto_refresh()
