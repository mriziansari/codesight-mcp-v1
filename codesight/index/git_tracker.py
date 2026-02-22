import pygit2
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class GitInfo:
    is_repo: bool
    last_commit: Optional[str]
    branch: Optional[str]
    file_history: dict  # path -> list of commits

class GitTracker:
    def __init__(self, repo_path: Path):
        self.path = repo_path
        self.repo = self._open_repo()
        
    def _open_repo(self) -> Optional[pygit2.Repository]:
        try:
            return pygit2.Repository(self.path)
        except pygit2.GitError:
            return None
            
    def is_valid(self) -> bool:
        return self.repo is not None
        
    def get_file_blame(self, file_path: Path) -> List[dict]:
        """Get line-by-line blame for file"""
        if not self.repo:
            return []
            
        try:
            blame = self.repo.blame(str(file_path.relative_to(self.path)))
            lines = []
            for hunk in blame:
                commit = hunk.final_committer
                lines.append({
                    "line_start": hunk.final_start_line_number,
                    "lines_in_hunk": hunk.lines_in_hunk,
                    "author": commit.name,
                    "email": commit.email,
                    "time": commit.time
                })
            return lines
        except Exception:
            return []