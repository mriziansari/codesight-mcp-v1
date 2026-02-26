from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
import networkx as nx
from tree_sitter import Parser, Language
import tree_sitter_python as tspython

from codesight.parsers.import_extractor import ImportExtractor
from codesight.index.file_discovery import FileDiscovery

@dataclass
class DependencyEdge:
    """
    Represents one dependency relationship between two files.
    
    source: File that imports (e.g., "auth.py")
    target: File being imported (e.g., "database.py")  
    symbols: What specifically is imported (e.g., ["get_connection"])
    line: Where in source file the import happens
    """
    source: str          # Relative path of importer
    target: str          # Relative path of imported file
    symbols: List[str]   # Specific functions/classes imported
    line: int            # Line number in source file
    is_relative: bool    # True for "from . import", False for absolute

class DependencyGraph:
    """
    Builds and queries a directed graph of file dependencies.
    
    Uses NetworkX for graph algorithms (shortest path, cycles, centrality).
    """
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.graph = nx.DiGraph()  # Directed graph: A → B means A depends on B
        parser = Parser()
        parser.language = Language(tspython.language())
        self.parser = parser
        self.import_extractor = ImportExtractor()
        
        # Map module names to file paths
        # "database" → "src/database.py"
        self.module_map: Dict[str, str] = {}
        
    def build(self):
        """
        Main entry point: scan all files, build complete dependency graph.
        """
        # Step 1: Discover all Python files and build module map
        discovery = FileDiscovery(self.root)
        py_files = [f for f in discovery.discover() if f.suffix == '.py']
        
        for file_path in py_files:
            relative = str(file_path.relative_to(self.root))
            self.graph.add_node(relative)  # Add file as node
            
            # Map module name to file
            # "src/database.py" → module "src.database" or just "database"
            module_name = self._path_to_module(relative)
            self.module_map[module_name] = relative
            
            # Also map simple name (last part)
            simple_name = relative.replace('/', '.').replace('.py', '')
            self.module_map[simple_name] = relative
        
        # Step 2: Parse each file, find imports, add edges
        for file_path in py_files:
            self._analyze_file(file_path)
    
    def _path_to_module(self, relative_path: str) -> str:
        """
        Convert file path to Python module name.
        
        "src/database.py" → "src.database"
        "utils.py" → "utils"
        """
        return relative_path.replace('/', '.').replace('.py', '')
    
    def _analyze_file(self, file_path: Path):
        """
        Parse single file, extract imports, resolve to file paths, add edges.
        """
        relative = str(file_path.relative_to(self.root))
        
        try:
            code = file_path.read_text(encoding='utf-8')
        except Exception:
            return
        
        # Parse with Tree-sitter
        tree = self.parser.parse(code.encode())
        imports = self.import_extractor.extract(tree.root_node, code, relative)
        
        # Resolve each import to actual file path
        for imp in imports:
            if imp['statement_type'] == 'from':
                target_file = self._resolve_import(imp, relative)
                if target_file:
                    # Extract imported symbol names
                    symbols = [s['name'] for s in imp.get('imported_names', [])]
                    
                    # Create edge
                    edge = DependencyEdge(
                        source=relative,
                        target=target_file,
                        symbols=symbols,
                        line=0,  # TODO: extract actual line number
                        is_relative=imp['is_relative']
                    )
                    
                    # Add to graph
                    self.graph.add_edge(relative, target_file, data=edge)
    
    def _resolve_import(self, import_info: dict, current_file: str) -> str:
        """
        Convert import statement to actual file path.
        
        Handles:
        - Absolute: from database import ... → look up in module_map
        - Relative: from . import ... → resolve relative to current file
        """
        module = import_info.get('module')
        is_relative = import_info['is_relative']
        level = import_info['level']  # 0 = absolute, 1 = same dir, 2 = parent dir
        
        if not is_relative:
            # Absolute import: from database import ...
            # Try full module name, then simple name
            if module in self.module_map:
                return self.module_map[module]
            
            # Try last component: "src.database" → "database"
            if '.' in module:
                simple = module.split('.')[-1]
                if simple in self.module_map:
                    return self.module_map[simple]
        
        else:
            # Relative import: from . import ..., from ..models import ...
            current_parts = current_file.split('/')
            
            # Go up 'level' directories
            if level < len(current_parts):
                base_path = '/'.join(current_parts[:-level]) if level > 0 else current_file
            else:
                return None  # Invalid relative import
            
            # If module specified: from .database import ...
            if module:
                target = f"{base_path}/{module.replace('.', '/')}.py"
                # Check if file exists in our graph
                if target in self.graph:
                    return target
            else:
                # from . import ... (import from __init__.py or current dir)
                init_file = f"{base_path}/__init__.py"
                if init_file in self.graph:
                    return init_file
        
        return None
    
    def get_dependencies(self, file_path: str) -> List[str]:
        """
        Get all files that 'file_path' directly depends on (outgoing edges).
        
        auth.py → [database.py, utils.py]
        """
        if file_path in self.graph:
            return list(self.graph.successors(file_path))
        return []
    
    def get_dependents(self, file_path: str) -> List[str]:
        """
        Get all files that depend on 'file_path' (incoming edges).
        
        database.py → [auth.py, models.py]
        """
        if file_path in self.graph:
            return list(self.graph.predecessors(file_path))
        return []
    
    def get_impact(self, file_path: str) -> Dict[str, any]:
        """
        Analyze impact of changing a file: what else might break?
        
        Returns all downstream files (transitive closure).
        """
        if file_path not in self.graph:
            return {'error': 'File not in graph'}
        
        # Find all files reachable from this file (BFS/DFS)
        # If A → B → C, then changing A affects B and C
        affected = set()
        to_visit = [file_path]
        
        while to_visit:
            current = to_visit.pop()
            for dependent in self.graph.predecessors(current):
                if dependent not in affected:
                    affected.add(dependent)
                    to_visit.append(dependent)
        
        return {
            'file': file_path,
            'direct_dependents': list(self.graph.predecessors(file_path)),
            'transitive_dependents': list(affected),
            'total_affected': len(affected),
            'risk_score': len(affected) / len(self.graph) if self.graph else 0
        }