from pathlib import Path
from typing import Iterator
import fnmatch
from codesight.config import settings

class FileDiscovery:
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()
    
    def discover(self) -> Iterator[Path]:
        """Discover files to index based on patterns"""
        for file_path in self.root_path.rglob("*"):
            if not file_path.is_file():
                continue
            relative_path = file_path.relative_to(self.root_path)
            str_path = str(relative_path)

            # Check ignore patterns
            parts = relative_path.parts
            should_ignore = False
            for part in parts:
                if any(fnmatch.fnmatch(part, pattern) for pattern in settings.ignore_patterns):
                    should_ignore = True
                    break
            if should_ignore:
                continue

            #  Check watch patterns
            if any(fnmatch.fnmatch(file_path.name, pat) for pat in settings.watch_patterns):
                yield file_path

    def count(self) -> int:
        """Total number of files to index"""
        return sum(1 for _ in self.discover())