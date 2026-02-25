from tree_sitter import Language, Parser
import tree_sitter_python as ts_python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Symbol:
    name: str            #Function/Class name
    type: str            # 'function', 'method', 'class', 'module'
    start_line: int      #Where it starts
    end_line: int        #Where it ends
    docstring: Optional[str] = None #Docstring of the function/class

class PythonParser:
    def __init__(self):
        self.parser = Parser()
        self.parser.language = Language(ts_python.language())
        
    def parse(self, code: str) -> List[Symbol]:
        """Extract all functions, classes, and methods from a Python file"""
        tree = self.parser.parse(code.encode())
        root = tree.root_node
        
        symbols = []
        
        for child in root.children:
            if child.type == "function_definition":
                symbol = self._extract_function(child, code)
                symbols.append(symbol)
            elif child.type == "class_definition":
                symbol = self._extract_class(child, code)
                symbols.append(symbol)
        
        return symbols

    def _extract_function(self, node, code: str) -> Symbol:
        """Get funtion name, lines, docstring from AST node"""
        
        #Find name
        name_node = node.child_by_field_name("name")
        name = code[name_node.start_byte:name_node.end_byte]

        #Find start and end lines
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        #Find docstring
        docstring = None
        body = node.child_by_field_name('body')
        if body and body.children:
            first_stmt = body.children[0]
            if first_stmt.type == 'expression_statement':
                string_node = first_stmt.children[0]
                if string_node.type == 'string':
                    docstring = code[string_node.start_byte:string_node.end_byte]
        
        return Symbol(
            name=name,
            type="function",
            start_line=start_line,
            end_line=end_line,
            docstring=docstring
        )
        
    def _extract_class(self, node, code: str) -> Symbol:
        """Similar to function, but type='class'"""
        name_node = node.child_by_field_name('name')
        name = code[name_node.start_byte:name_node.end_byte]
        
        return Symbol(
            name=name,
            type="class",
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            docstring=None  # Simplified for now
        )
        
        
