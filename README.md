# jsonfix

Parse "almost JSON" with trailing commas, comments, smart quotes - with repair logging.

## Installation

```bash
pip install jsonfix
```

## Quick Start

```python
from jsonfix import loads_relaxed

# Parse JSON with trailing commas, comments, and smart quotes
data = loads_relaxed('''
{
    // Configuration settings
    "name": "example",
    "items": [1, 2, 3,],  // trailing comma OK
}
''')
print(data)  # {'name': 'example', 'items': [1, 2, 3]}
```

## Features

- **Trailing commas**: `{"a": 1,}` and `[1, 2, 3,]`
- **Comments**: `//`, `#`, and `/* */` style
- **Smart quotes**: Automatically converts curly quotes to straight quotes
- **Repair log**: Track exactly what was fixed (unique feature!)

## Repair Logging

```python
from jsonfix import loads_relaxed, Repair

repairs = []
data = loads_relaxed('{"a": 1, /* comment */ "b": 2,}', repair_log=repairs)

for repair in repairs:
    print(f"{repair.kind}: {repair.message}")
# MULTI_LINE_COMMENT: Removed comment '/* comment */'
# TRAILING_COMMA: Removed trailing comma
```

## API

### `loads_relaxed(s, *, strict=False, allow_trailing_commas=True, allow_comments=True, normalize_quotes=True, repair_log=None, on_repair="ignore")`

Parse a relaxed JSON string.

**Parameters:**
- `s`: JSON string (possibly with relaxed syntax)
- `strict`: If `True`, disable all relaxations (use standard `json.loads`)
- `allow_trailing_commas`: Allow trailing commas in arrays/objects
- `allow_comments`: Allow `//`, `#`, and `/* */` comments
- `normalize_quotes`: Convert smart quotes to straight quotes
- `repair_log`: Optional list to collect `Repair` objects
- `on_repair`: Action when repair needed - `"ignore"`, `"warn"`, or `"error"`

### `load_relaxed(fp, **kwargs)`

Like `loads_relaxed` but reads from a file-like object.

### `can_parse(s)`

Check if a string can be parsed (with relaxations).

### `get_repairs(s)`

Get list of repairs needed without actually parsing.

## License

MIT
