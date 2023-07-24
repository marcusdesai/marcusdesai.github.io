
__all__ = ["make_handlers"]

from collections.abc import Iterator
from pathlib import Path
from queue import Queue
from threading import Lock
from tooling.wysiwyg.driver import BASE_URL, Driver
from watchdog.events import FileModifiedEvent, FileSystemEvent, FileSystemEventHandler

LOCK = Lock()


# We set return type to str arbitrarily because we know it will be str
def drain_queue(q: Queue) -> Iterator[str]:
    while not q.empty():
        yield q.get(block=False)


class OutputHandler(FileSystemEventHandler):
    def __init__(self, content_changes: Queue) -> None:
        self.driver = Driver()
        self.content_changes = content_changes

    def on_modified(self, event: FileSystemEvent) -> None:
        if not isinstance(event, FileModifiedEvent):
            return None
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
    def __init__(self, content_changes: Queue) -> None:
        self.content_changes = content_changes

    def on_modified(self, event: FileSystemEvent) -> None:
        if isinstance(event, FileModifiedEvent):
            path = str(event.src_path)
            if not path.endswith("~"):
                with LOCK:
                    self.content_changes.put(event.src_path, block=False)


def make_handlers() -> tuple[OutputHandler, ContentHandler]:
    queue = Queue()
    output_handler = OutputHandler(queue)
    content_handler = ContentHandler(queue)
    return output_handler, content_handler
