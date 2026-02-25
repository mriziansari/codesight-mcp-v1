from codesight.parsers.python_parser import PythonParser

code = '''
def authenticate_user(username, password):
    """Check if user credentials are valid."""
    return username == "admin" and password == "secret"

class UserManager:
    def get_user(self, id):
        return {"id": id}
'''

parser = PythonParser()
symbols = parser.parse(code)

for sym in symbols:
    print(f"{sym.type}: {sym.name} (lines {sym.start_line}-{sym.end_line})")
    if sym.docstring:
        print(f"  Doc: {sym.docstring[:50]}...")