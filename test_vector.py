from pathlib import Path
from codesight.index.file_reader import FileReader
from codesight.index.vector_store import VectorStore

# Setup
root = Path("/Volumes/Work/AI Work/AI Learning")
reader = FileReader(root)
store = VectorStore(Path(".codesight/vectors"))

# Read and index one file
test_file = list(root.rglob("*.py"))[0]
print(f"Indexing: {test_file.name}")

content = reader.read(test_file)
chunk_ids = store.add_file(content)
print(f"Added {len(chunk_ids)} chunks")

# Search
print("\nSearching: 'how to classify text'")
results = store.search("how to classify text", n_results=3)

for r in results:
    print(f"\n{r['metadata']['symbol_name']} ({r['metadata']['symbol_type']})")
    print(f"File: {r['metadata']['file_path']}")
    print(f"Score: {1 - r['distance']:.3f}")  # Convert distance to similarity
    print(f"Code preview: {r['content'][:100]}...")