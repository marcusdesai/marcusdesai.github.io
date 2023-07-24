import time
from tooling.wysiwyg.handler import make_handlers
from watchdog.observers import Observer


def hot_reload() -> None:
    output_handler, content_handler = make_handlers()
    observer = Observer()
    observer.schedule(content_handler, "content", recursive=True)
    observer.schedule(output_handler, "output", recursive=True)
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
    hot_reload()
