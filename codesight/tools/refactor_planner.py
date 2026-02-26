from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

from codesight.index.dependency_graph import DependencyGraph
from codesight.index.vector_store import VectorStore

@dataclass
class ChangeStep:
    file: str
    line: int
    original: str
    replacement: str
    reason: str

class RefactorPlanner:
    """
    Plans multi-file refactoring operations.
    
    Combines semantic search, dependency graph, and code analysis
    to generate safe, ordered refactoring steps.
    """
    
    def __init__(self, root_path: Path, vector_store: VectorStore, graph: DependencyGraph):
        self.root = root_path
        self.vector_store = vector_store
        self.graph = graph
    
    def plan_rename(self, old_name: str, new_name: str, file_hint: Optional[str] = None) -> Dict:
        """
        Plan renaming a function, class, or variable across codebase.
        
        Steps:
        1. Find definition (search or file_hint)
        2. Find all files importing it
        3. Find all call sites
        4. Generate ordered changes (definition last)
        """
        
        # Step 1: Find where symbol is defined
        definition = self._find_definition(old_name, file_hint)
        if not definition:
            return {'error': f"Could not find definition of '{old_name}'"}
        
        # Step 2: Find files that depend on this symbol
        dependent_files = self._find_dependents(definition['file'], old_name)
        
        # Step 3: Analyze each file for call sites
        changes = []
        
        for dep_file in dependent_files:
            file_changes = self._analyze_file_for_symbol(dep_file, old_name, new_name)
            changes.extend(file_changes)
        
        # Step 4: Add definition change (do last to avoid breaking during refactor)
        changes.append(ChangeStep(
            file=definition['file'],
            line=definition['line'],
            original=f"def {old_name}(",  # Simplified pattern
            replacement=f"def {new_name}(",
            reason=f"Rename function definition"
        ))
        
        # Sort: dependents first, definition last
        changes.sort(key=lambda c: (c.file == definition['file'], c.file))
        
        return {
            'symbol': old_name,
            'new_name': new_name,
            'definition_file': definition['file'],
            'total_changes': len(changes),
            'files_affected': len(set(c.file for c in changes)),
            'risk_level': self._calculate_risk(changes),
            'steps': [
                {
                    'file': c.file,
                    'line': c.line,
                    'change': f"{c.original} → {c.replacement}",
                    'reason': c.reason
                }
                for c in changes
            ],
            'suggested_order': self._suggest_order(changes)
        }
    
    def _find_definition(self, symbol_name: str, file_hint: Optional[str]) -> Optional[Dict]:
        """
        Find where a symbol is defined.
        Try file_hint first, then search vector store.
        """
        if file_hint:
            # Check specific file
            file_path = self.root / file_hint
            if file_path.exists():
                content = file_path.read_text()
                # Simple regex to find function definition
                pattern = rf"def\s+{re.escape(symbol_name)}\s*\("
                for i, line in enumerate(content.splitlines(), 1):
                    if re.search(pattern, line):
                        return {'file': file_hint, 'line': i, 'content': line.strip()}
        
        # Search vector store for definition
        results = self.vector_store.search(f"def {symbol_name}", n_results=5)
        for r in results:
            if symbol_name in r['metadata'].get('symbol_name', ''):
                return {
                    'file': r['metadata']['file_path'],
                    'line': r['metadata']['start_line'],
                    'content': r['content'][:100]
                }
        
        return None
    
    def _find_dependents(self, definition_file: str, symbol_name: str) -> List[str]:
        """
        Find all files that might use this symbol.
        """
        # Direct dependents from graph
        direct = self.graph.get_dependents(definition_file)
        
        # Also search for imports of the symbol
        # This catches dynamic imports or imports not in graph
        search_results = self.vector_store.search(
            f"import {symbol_name} or from {definition_file.replace('/', '.')} import {symbol_name}",
            n_results=10
        )
        
        from_search = [r['metadata']['file_path'] for r in search_results]
        
        # Combine and deduplicate
        all_files = set(direct + from_search + [definition_file])
        return list(all_files)
    
    def _analyze_file_for_symbol(self, file_path: str, old_name: str, new_name: str) -> List[ChangeStep]:
        """
        Find all call sites of a symbol in a file.
        """
        changes = []
        full_path = self.root / file_path
        
        try:
            content = full_path.read_text()
            lines = content.splitlines()
        except Exception:
            return changes
        
        # Patterns to match:
        # 1. Direct call: old_name(
        # 2. Method call: obj.old_name(
        # 3. Import: from x import old_name
        
        call_pattern = rf"\b{re.escape(old_name)}\s*\("
        import_pattern = rf"from\s+\S+\s+import\s+.*\b{re.escape(old_name)}\b"
        
        for i, line in enumerate(lines, 1):
            # Skip comments and strings (simplified)
            code_only = line.split('#')[0]
            
            # Skip if this is the definition line (we handle it separately)
            if re.match(rf"^\s*def\s+{re.escape(old_name)}\b", code_only):
                continue
                
            if re.search(call_pattern, code_only):
                changes.append(ChangeStep(
                    file=file_path,
                    line=i,
                    original=line.strip(),
                    replacement=line.replace(old_name, new_name).strip(),
                    reason=f"Update call to {old_name}"
                ))
            elif re.search(import_pattern, code_only):
                changes.append(ChangeStep(
                    file=file_path,
                    line=i,
                    original=line.strip(),
                    replacement=line.replace(old_name, new_name).strip(),
                    reason=f"Update import of {old_name}"
                ))
        
        return changes
    
    def _calculate_risk(self, changes: List[ChangeStep]) -> str:
        """Assess risk level based on number of changes and file criticality."""
        num_changes = len(changes)
        num_files = len(set(c.file for c in changes))
        
        if num_changes == 0:
            return "unknown"
        elif num_changes == 1:
            return "low"
        elif num_files <= 2:
            return "medium"
        elif num_files <= 5:
            return "high"
        else:
            return "critical"
    
    def _suggest_order(self, changes: List[ChangeStep]) -> str:
        """Suggest execution order for changes."""
        files = list(dict.fromkeys(c.file for c in changes))  # Preserve order, unique
        
        if len(files) <= 3:
            return "Change all files in one commit: " + ", ".join(files)
        else:
            return f"Change in {len(files)} phases: tests first, then internals, then API surface"