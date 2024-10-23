from dataclasses import dataclass
from typing import Callable
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskID
from rich.text import Text
import uuid
from urllib.parse import urlparse, parse_qs
import re

console = Console()

class ProgressManager:
    def __init__(self):
        self.console = Console()
        self.tasks = {}

    def get_callback(self, total: int, desc: str):
        track_id = self.extract_track_id(desc)
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {"total": total, "completed": 0, "desc": desc, "track_id": track_id}

        def _callback_update(x: int):
            self.tasks[task_id]["completed"] += x
            self._print_progress(task_id)

        def _callback_done():
            self._print_progress(task_id, done=True)
            del self.tasks[task_id]

        return Handle(_callback_update, _callback_done)

    def _print_progress(self, task_id: str, done: bool = False):
        task = self.tasks[task_id]
        percentage = (task["completed"] / task["total"]) * 100
        status = "Completed" if done else "Downloading"
        description = task['desc']
        track_id = task['track_id']
        self.console.print(f"{status}: {description} {task['completed']}/{task['total']} ({percentage:.1f}%)")

    def add_title(self, title: str):
        self.console.print(f"Added task: {title}")

    def remove_title(self, title: str):
        self.console.print(f"Removed task: {title}")

    def extract_track_id(self, desc: str) -> str:
        # For Deezer
        deezer_match = re.search(r'media\/.*\/(\d+)', desc)
        if deezer_match:
            return deezer_match.group(1)
        # For Qobuz
        qobuz_query = parse_qs(urlparse(desc).query)
        if 'eid' in qobuz_query:
            return qobuz_query['eid'][0]
        # For Tidal
        tidal_match = re.search(r'tidal\.com/.*?/(\d+)', desc)
        if tidal_match:
            return tidal_match.group(1)
        return "Unknown"

@dataclass(slots=True)
class Handle:
    update: Callable[[int], None]
    done: Callable[[], None]

    def __enter__(self):
        return self.update

    def __exit__(self, *_):
        self.done()

# global instance
_p = ProgressManager()

def get_progress_callback(enabled: bool, total: int, desc: str) -> Handle:
    global _p
    if not enabled:
        return Handle(lambda _: None, lambda: None)
    return _p.get_callback(total, desc)

def add_title(title: str):
    global _p
    _p.add_title(title)

def remove_title(title: str):
    global _p
    _p.remove_title(title)

def clear_progress():
    global _p
