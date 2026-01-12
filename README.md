# jsonfix

Parse "almost JSON" with trailing commas, comments, smart quotes, and more.

**Unique feature**: Repair logging to see exactly what was fixed - invaluable for debugging and auditing.

## Installation

### From PyPI

```bash
pip install jsonfix
```

### From Source

```bash
git clone https://github.com/Broadhead-Logic/jsonfix.git
cd jsonfix
pip install -e .
```

### Development

```bash
pip install -e ".[dev]"
pytest  # Run tests (365 tests, 98% coverage)
```

## Quick Start

```python
from jsonfix import loads_relaxed

# Parse JSON with common issues
data = loads_relaxed('''
{
    // Configuration
    "name": "example",
    "items": [1, 2, 3,],  // trailing comma OK
}
''')
print(data)  # {'name': 'example', 'items': [1, 2, 3]}
```

### With Repair Logging

```python
from jsonfix import loads_relaxed, Repair

repairs = []
data = loads_relaxed('{"a": 1, /* comment */ "b": 2,}', repair_log=repairs)

for repair in repairs:
    print(f"Line {repair.line}: {repair.message}")
# Line 1: Removed multi-line comment '/* comment */'
# Line 1: Removed trailing comma
```

## Features

jsonfix handles 9 types of relaxed JSON syntax. All features are enabled by default.

### 1. Trailing Commas

```python
>>> loads_relaxed('{"items": [1, 2, 3,],}')
{'items': [1, 2, 3]}
```

### 2. Single-Line Comments (`//`)

```python
>>> loads_relaxed('''
... {
...     "host": "localhost",  // development server
...     "port": 8080
... }
... ''')
{'host': 'localhost', 'port': 8080}
```

### 3. Hash Comments (`#`)

```python
>>> loads_relaxed('''
... {
...     # Database configuration
...     "db_host": "localhost"
... }
... ''')
{'db_host': 'localhost'}
```

### 4. Multi-Line Comments (`/* */`)

```python
>>> loads_relaxed('''
... {
...     /* This is a
...        multi-line comment */
...     "enabled": true
... }
... ''')
{'enabled': True}
```

### 5. Smart Quote Normalization

Automatically converts curly/smart quotes (from Word, Google Docs, email) to straight quotes:

```python
>>> loads_relaxed('{"message": "Hello world"}')  # curly quotes
{'message': 'Hello world'}
```

### 6. Single-Quote Strings

```python
>>> loads_relaxed("{'name': 'Alice', 'age': 30}")
{'name': 'Alice', 'age': 30}
```

### 7. Unquoted Keys

```python
>>> loads_relaxed('{name: "Alice", age: 30}')
{'name': 'Alice', 'age': 30}
```

### 8. Python Literals

Converts Python `True`, `False`, `None` to JSON equivalents:

```python
>>> loads_relaxed('{"active": True, "data": None}')
{'active': True, 'data': None}
```

### 9. Auto-Close Brackets

Adds missing closing brackets at end of input (useful for truncated LLM output):

```python
>>> loads_relaxed('{"user": {"name": "Alice"')
{'user': {'name': 'Alice'}}
```

### 10. Ellipsis Removal

Removes truncation markers from arrays/objects:

```python
>>> loads_relaxed('[1, 2, 3, ...]')
[1, 2, 3]

>>> loads_relaxed('{"a": 1, "b": 2, ...}')
{'a': 1, 'b': 2}
```

### 11. Newline Escaping

Escapes literal newlines inside strings:

```python
>>> loads_relaxed('{"text": "line1\nline2"}')
{'text': 'line1\nline2'}
```

## API Reference

### `loads_relaxed()`

Parse a relaxed JSON string into Python objects.

```python
def loads_relaxed(
    s: str,
    *,
    strict: bool = False,
    allow_trailing_commas: bool = True,
    allow_comments: bool = True,
    normalize_quotes: bool = True,
    allow_single_quote_strings: bool = True,
    allow_unquoted_keys: bool = True,
    convert_python_literals: bool = True,
    escape_newlines: bool = True,
    auto_close_brackets: bool = True,
    remove_ellipsis: bool = True,
    repair_log: list[Repair] | None = None,
    on_repair: Literal["ignore", "warn", "error"] = "ignore",
) -> Any
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `s` | `str` | required | JSON string to parse |
| `strict` | `bool` | `False` | Disable all relaxations, use standard `json.loads` |
| `allow_trailing_commas` | `bool` | `True` | Allow `{"a": 1,}` and `[1, 2,]` |
| `allow_comments` | `bool` | `True` | Allow `//`, `#`, and `/* */` comments |
| `normalize_quotes` | `bool` | `True` | Convert smart/curly quotes to straight quotes |
| `allow_single_quote_strings` | `bool` | `True` | Convert `'string'` to `"string"` |
| `allow_unquoted_keys` | `bool` | `True` | Quote unquoted keys like `{key: 1}` |
| `convert_python_literals` | `bool` | `True` | Convert `True`/`False`/`None` to JSON |
| `escape_newlines` | `bool` | `True` | Escape literal newlines in strings |
| `auto_close_brackets` | `bool` | `True` | Add missing `]` or `}` at end of input |
| `remove_ellipsis` | `bool` | `True` | Remove `...` or `...` truncation markers |
| `repair_log` | `list[Repair]` | `None` | List to collect `Repair` objects |
| `on_repair` | `str` | `"ignore"` | Action on repair: `"ignore"`, `"warn"`, `"error"` |

#### Returns

Parsed Python object (`dict`, `list`, `str`, `int`, `float`, `bool`, or `None`).

#### Raises

- `json.JSONDecodeError`: If JSON is invalid even after relaxations
- `ValueError`: If `on_repair="error"` and repairs are needed

### `load_relaxed()`

Parse relaxed JSON from a file-like object.

```python
def load_relaxed(fp: IO[str], **kwargs) -> Any
```

```python
with open('config.json') as f:
    data = load_relaxed(f)
```

### `can_parse()`

Check if a string can be parsed (with relaxations).

```python
def can_parse(s: str) -> bool
```

```python
>>> can_parse('{"a": 1,}')
True
>>> can_parse('{invalid')
False
```

### `get_repairs()`

Get list of repairs needed without raising errors.

```python
def get_repairs(s: str) -> list[Repair]
```

```python
>>> repairs = get_repairs('{"a": 1, /* x */}')
>>> for r in repairs:
...     print(r.kind, r.message)
RepairKind.MULTI_LINE_COMMENT Removed multi-line comment '/* x */'
RepairKind.TRAILING_COMMA Removed trailing comma
```

### `Repair` Dataclass

Record of a single repair made during parsing.

```python
@dataclass
class Repair:
    kind: RepairKind      # Type of repair (enum)
    position: int         # Character position (0-indexed)
    line: int             # Line number (1-indexed)
    column: int           # Column number (1-indexed)
    original: str         # Original text that was repaired
    replacement: str      # Replacement text (empty if removed)
    message: str          # Human-readable description
```

### `RepairKind` Enum

Types of repairs that can be made:

| Value | Description |
|-------|-------------|
| `TRAILING_COMMA` | Removed trailing comma |
| `SINGLE_LINE_COMMENT` | Removed `//` comment |
| `MULTI_LINE_COMMENT` | Removed `/* */` comment |
| `HASH_COMMENT` | Removed `#` comment |
| `SMART_QUOTE` | Normalized smart quote to straight quote |
| `SINGLE_QUOTE_STRING` | Converted `'string'` to `"string"` |
| `UNQUOTED_KEY` | Added quotes around unquoted key |
| `PYTHON_LITERAL` | Converted `True`/`False`/`None` |
| `UNESCAPED_NEWLINE` | Escaped literal newline in string |
| `MISSING_BRACKET` | Added missing closing bracket |
| `TRUNCATION_MARKER` | Removed `...` ellipsis marker |

## Configuration

### Disabling Specific Features

Disable individual features by setting parameters to `False`:

```python
# Only allow comments, reject other relaxations
data = loads_relaxed(
    text,
    allow_trailing_commas=False,
    allow_single_quote_strings=False,
    allow_unquoted_keys=False,
    convert_python_literals=False,
    auto_close_brackets=False,
    remove_ellipsis=False,
)
```

### Strict Mode

Use `strict=True` to disable all relaxations and use standard `json.loads`:

```python
>>> loads_relaxed('{"a": 1}', strict=True)  # Valid JSON works
{'a': 1}

>>> loads_relaxed('{"a": 1,}', strict=True)  # Trailing comma fails
JSONDecodeError: ...
```

### Error Handling Modes

Control behavior when repairs are needed with `on_repair`:

```python
# Ignore repairs (default) - parse silently
data = loads_relaxed(text, on_repair="ignore")

# Warn on repairs - emit warnings via warnings.warn()
import warnings
with warnings.catch_warnings(record=True) as w:
    data = loads_relaxed(text, on_repair="warn")
    for warning in w:
        print(warning.message)

# Error on repairs - raise ValueError on first repair needed
try:
    data = loads_relaxed(text, on_repair="error")
except ValueError as e:
    print(f"Repair needed: {e}")
```

## Real-World Examples

### Parsing LLM Output

LLMs often produce JSON with trailing commas or Python literals:

```python
llm_response = '''
{
    "analysis": "The data shows positive trends",
    "confidence": 0.85,
    "factors": [
        "market growth",
        "user adoption",
    ],
    "recommend": True,
}
'''

data = loads_relaxed(llm_response)
# {'analysis': 'The data shows positive trends', 'confidence': 0.85, ...}
```

### Config Files (VS Code Style)

Parse JSONC-style config files with comments:

```python
config = '''
{
    // Editor settings
    "editor.fontSize": 14,
    "editor.tabSize": 2,

    /* Formatting options */
    "editor.formatOnSave": true,
    "editor.wordWrap": "on",
}
'''

settings = loads_relaxed(config)
```

### TypeScript Config (tsconfig.json)

```python
tsconfig = '''
{
    "compilerOptions": {
        "target": "ES2020",
        "module": "commonjs",
        /* Strict type checking */
        "strict": true,
        "esModuleInterop": true,
    },
    "include": ["src/**/*",],
    "exclude": ["node_modules",],
}
'''

config = loads_relaxed(tsconfig)
```

### Copy-Paste from Word/Email

Text copied from Word or email often has smart quotes:

```python
# These curly quotes would break standard json.loads
pasted = '{"title": "Meeting Notes", "author": "John"}'

data = loads_relaxed(pasted)
# {'title': 'Meeting Notes', 'author': 'John'}
```

### Truncated API Responses

Handle truncated JSON from logs or debugging:

```python
truncated = '{"users": [{"name": "Alice"}, {"name": "Bob"'

data = loads_relaxed(truncated)
# {'users': [{'name': 'Alice'}, {'name': 'Bob'}]}
```

### Debugging with Repair Log

Track exactly what was fixed:

```python
repairs = []
data = loads_relaxed('''
{
    // Config file
    name: 'MyApp',
    version: "1.0",
    enabled: True,
}
''', repair_log=repairs)

print(f"Made {len(repairs)} repairs:")
for r in repairs:
    print(f"  Line {r.line}, col {r.column}: {r.message}")
# Made 5 repairs:
#   Line 2, col 5: Removed single-line comment '// Config file'
#   Line 3, col 5: Added quotes around unquoted key 'name'
#   Line 3, col 11: Converted single-quoted string 'MyApp' to double quotes
#   Line 5, col 14: Converted Python literal 'True' to JSON 'true'
#   Line 6, col 1: Removed trailing comma
```

## License

MIT

## Requirements

- Python 3.9+
- No external dependencies (uses only standard library)
