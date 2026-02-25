from pathlib import Path
from codesight.index.file_reader import FileReader

reader = FileReader(Path("/Volumes/Work/AI Work/AI Learning"))

# Find first Python file
test_file = list(Path("/Volumes/Work/AI Work/AI Learning").rglob("*.py"))[0]
print(f"Testing: {test_file}")

content = reader.read(test_file)
print(f"Found {len(content.symbols)} symbols:")
for sym in content.symbols[:5]:  # First 5
    print(f"  - {sym.type}: {sym.name}")