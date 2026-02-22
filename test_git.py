from pathlib import Path
from codesight.index.git_tracker import GitTracker

# Test on your AI Learning project
tracker = GitTracker(Path("/Volumes/Work/AI Work/AI Learning/rag_learning"))

print(f"Is valid git repo: {tracker.is_valid()}")

if tracker.is_valid():
    # Test blame on a Python file
    test_file = Path("/Volumes/Work/AI Work/AI Learning/rag_learning").glob("*.py")
    first_py = next(test_file, None)
    
    if first_py:
        blame = tracker.get_file_blame(first_py)
        print(f"\nBlame for {first_py.name}:")
        for line in blame[:5]:  # First 5 hunks
            print(f"  Line {line['line_start']}: {line['author']} ({line['email']})")