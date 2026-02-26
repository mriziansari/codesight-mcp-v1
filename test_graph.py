from pathlib import Path
from codesight.index.dependency_graph import DependencyGraph

# Test on your AI Learning project
root = Path("/Volumes/Work/AI Work/AI Learning")
graph = DependencyGraph(root)

print("Building dependency graph...")
graph.build()

print(f"\nTotal files: {len(graph.graph.nodes)}")
print(f"Total dependencies: {len(graph.graph.edges)}")

# Find most connected file (highest impact)
max_deps = 0
max_file = None
for node in graph.graph.nodes:
    deps = len(graph.get_dependents(node))
    if deps > max_deps:
        max_deps = deps
        max_file = node

print(f"\nMost impactful file: {max_file}")
print(f"Used by {max_deps} other files")

# Test impact analysis
if max_file:
    impact = graph.get_impact(max_file)
    print(f"\nImpact analysis for {max_file}:")
    print(f"  Direct dependents: {len(impact['direct_dependents'])}")
    print(f"  Total affected: {impact['total_affected']}")
    print(f"  Risk score: {impact['risk_score']:.2%}")