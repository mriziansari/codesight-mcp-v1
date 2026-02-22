from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    codebase_path: Path = Path(".")
    index_dir: Path = Path(".codesight")
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 512
    watch_patterns: list[str] = ["*.py", "*.js", "*.ts", "*.go", "*.rs"]
    ignore_patterns: list[str] = ["__pycache__", "node_modules", ".git", "*.pyc"]
    
    class Config:
        env_prefix = "CODESIGHT_"

settings = Settings()