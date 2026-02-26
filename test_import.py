from tree_sitter import Parser, Language
import tree_sitter_python as tspython
from codesight.parsers.import_extractor import ImportExtractor

code = '''
import os
import numpy as np
from database import get_connection, close_connection
from . import utils
from ..models import User
from .auth import authenticate

def login():
    pass
'''

parser = Parser()
parser.language = Language(tspython.language())
tree = parser.parse(code.encode())
root = tree.root_node

extractor = ImportExtractor()
imports = extractor.extract(root, code, "test.py")

print(f"Found {len(imports)} imports:\n")
for imp in imports:
    if imp['statement_type'] == 'import':
        print(f"import: {imp['modules']}")
    else:
        rel = "relative" if imp['is_relative'] else "absolute"
        print(f"from {imp['module']} import {imp['imported_names']} ({rel}, level {imp['level']})")