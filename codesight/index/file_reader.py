from pathlib import Path
from dataclasses import dataclass
from typing import List
from codesight.parsers.python_parser import PythonParser, Symbol

@dataclass
class FileContent:
    path: Path          # Relative path
    content: str        # Full text
    language: str       # python, javascript, etc.
    line_count: int     # Total lines
    symbols: List[Symbol] = None # Extracted symbols
    
class FileReader:
    def __init__(self, root_path: Path):
        self.root = root_path
        self.python_parser = PythonParser()
        
    def read(self, file_path: Path) -> FileContent:
        """Read a single file and return structured content"""
        # Make relative to root
        relative_path = file_path.relative_to(self.root)
        
        # Detect language from extension
        language = self._detect_language(file_path.suffix)
        
        # Read content
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = file_path.read_text(encoding='latin-1')
        
        # Parse symbols
        symbols = []
        if language == 'python':
            symbols = self.python_parser.parse(content)
            
        return FileContent(
            path=relative_path,
            content=content,
            language=language,
            line_count=len(content.splitlines()),
            symbols=symbols
        )
    
    def _detect_language(self, suffix: str) -> str:
        """Map file extension to language"""
        mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.md': 'markdown'
        }
        return mapping.get(suffix, 'unknown')