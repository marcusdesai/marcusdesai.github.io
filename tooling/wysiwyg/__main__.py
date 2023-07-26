import time
from collections.abc import Iterator
from pathlib import Path
from queue import Queue
from selenium import webdriver
from threading import Lock
from typing import Any, Final
from watchdog.events import FileModifiedEvent, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

BASE_URL: Final[str] = "localhost:8000"
LOCK: Final[Lock] = Lock()


class Driver:
    def __init__(self) -> None:
        self.driver = webdriver.Firefox()
        self.page = BASE_URL
        self.driver.get(self.page)

    def refresh(self, url: str | None = None) -> None:
        if url is None or self.page == url:
            scroll_height = self.page_y_offset()
            self.driver.get(self.page)
            self.page_scroll_to(scroll_height)
        else:
            self.page = url
            self.driver.get(self.page)

    def page_y_offset(self) -> Any:  # noqa: ANN401
        return self.driver.execute_script("return window.pageYOffset")

    def page_scroll_to(self, scroll_height: Any) -> None:  # noqa: ANN401
        self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")


def drain_queue(q: Queue[str]) -> Iterator[str]:
    while not q.empty():
        yield q.get(block=False)


class OutputHandler(FileSystemEventHandler):
    def __init__(self, content_changes: Queue[str]) -> None:
        self.driver = Driver()
        self.content_changes = content_changes

    def on_modified(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileModifiedEvent):
            with LOCK:
                changed = list(drain_queue(self.content_changes))
            if len(changed) != 0:
                modified_path = Path(changed[-1])
                if not modified_path.suffix.endswith("md"):
                    return self.driver.refresh()
                url = f"{BASE_URL}/{modified_path.stem}.html"
                self.driver.refresh(url)
            else:
                self.driver.refresh()


class ContentHandler(FileSystemEventHandler):
    def __init__(self, content_changes: Queue[str]) -> None:
        self.content_changes = content_changes

    def on_modified(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileModifiedEvent):
            if not (path := str(event.src_path)).endswith("~"):
                with LOCK:
                    self.content_changes.put(path, block=False)


def auto_refresh() -> None:
    queue = Queue()
    observer = Observer()
    observer.schedule(ContentHandler(queue), "content", recursive=True)
    observer.schedule(OutputHandler(queue), "output", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    auto_refresh()
