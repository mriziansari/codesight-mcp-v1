from tree_sitter import Node
from typing import List, Tuple, Optional
import re

class ImportExtractor:
    """
    Extracts import relationships from Python AST.
    
    For each import statement, we capture:
    - What is being imported (module name)
    - Where it's imported from (source file)
    - What names are imported (specific functions/classes)
    """
    
    def extract(self, root_node: Node, code: str, current_file: str) -> List[dict]:
        """
        Walks AST, finds all import statements, returns structured data.
        
        Args:
            root_node: Tree-sitter root node of parsed file
            code: Full source code string
            current_file: Path of file being analyzed (for relative imports)
        
        Returns:
            List of import records with module names and imported symbols
        """

        imports = []
        for child in root_node.children:
            #Case 1 import x (import_statement)
            if child.type == "import_statement":
                import_info = self._parse_import_statement(child, code)
                imports.append(import_info)
            #Case 2 from x import y (import_from_statement)
            elif child.type == "import_from_statement":
                import_info = self._parse_import_from(child, code)
                imports.append(import_info)
        
        return imports
    
    def _parse_import_statement(self, node: Node, code: str) -> dict:
        """
        Parses: import os
                import numpy as np
        
        Returns module name and alias (if any).
        """
        # Get all children that are dotted_names (module names)
        modules = []
        for child in node.children:
            if child.type == "dotted_name":
                module_name = code[child.start_byte:child.end_byte]
                modules.append({'name': module_name, 'alias': None})
            elif child.type == "aliased_import":
                # import numpy as np
                name_node = child.child_by_field_name("name")
                alias_node = child.child_by_field_name("alias")
                if name_node:
                    name = code[name_node.start_byte:name_node.end_byte]
                    alias = code[alias_node.start_byte:alias_node.end_byte] if alias_node else None
                    modules.append({'name': name, 'alias': alias})
        
        return {
            'statement_type': 'import',
            'modules': modules,
            'is_relative': False,
            'level': 0
        }

    def _parse_import_from(self, node: Node, code: str) -> dict:
        """
        Parses: from database import get_connection
                from . import utils
                from ..models import User, Profile
        
        Returns source module and imported names.
        """
        # Find 'from' module (dotted_name or relative_import)
        from_module = None
        is_relative = False
        level = 0
        imported_names = []
        
        # Use a unified loop that handles everything consistently
        found_import_keyword = False
        
        for child in node.children:
            if child.type == 'import':
                found_import_keyword = True
                continue
            
            if not found_import_keyword:
                # Part before 'import'
                if child.type == 'dotted_name':
                    from_module = code[child.start_byte:child.end_byte]
                elif child.type == 'relative_import':
                    is_relative = True
                    text = code[child.start_byte:child.end_byte]
                    level = len(text) - len(text.lstrip('.'))
                    # Extract the name part if it exists (e.g. '..models')
                    for sub in child.children:
                        if sub.type == 'dotted_name':
                            from_module = code[sub.start_byte:sub.end_byte]
            else:
                # After 'import' keyword
                if child.type == 'dotted_name':
                    name = code[child.start_byte:child.end_byte]
                    imported_names.append({'name': name, 'alias': None})
                elif child.type == 'aliased_import':
                    name_node = child.child_by_field_name("name")
                    alias_node = child.child_by_field_name("alias")
                    if name_node:
                        name = code[name_node.start_byte:name_node.end_byte]
                        alias = code[alias_node.start_byte:alias_node.end_byte] if alias_node else None
                        imported_names.append({'name': name, 'alias': alias})
                # Note: commas and parentheses are skipped as they don't match these types
        
        return {
            'statement_type': 'from',
            'module': from_module,
            'is_relative': is_relative,
            'level': level,
            'imported_names': imported_names
        }