# PyCheck: Python AST Code Quality Checker

A lightweight command-line code-quality checker for Python source files. It reads a file, parses it into an Abstract Syntax Tree (AST), and reports common maintainability and correctness issues without executing the analyzed code.

The project uses only the Python standard library at runtime. Its test suite uses `pytest`.

## Features

- Analyzes one Python file from the command line.
- Parses the source once and shares the resulting AST across all checks.
- Produces filename and line-number diagnostics.
- Supports optional command-line overrides for numerical limits.
- Handles missing files, unreadable files, and syntax errors without tracebacks.
- Does not import or execute the file being analyzed.

## Supported checks

| Check | What it reports | Default |
| --- | --- | ---: |
| Missing docstrings | Functions without a docstring | No threshold |
| Function length | Functions longer than the allowed number of lines | 20 lines |
| Parameter count | Functions with too many parameters | 5 parameters |
| Bare `except` | `except:` clauses without an exception type | No threshold |
| Incorrect `None` comparison | Comparisons such as `value == None` or `value != None` | No threshold |
| Excessive nesting | Functions whose `if`, `for`, and `while` nesting is too deep | Depth 5 |
| Excessive branches | Functions with too many `elif` and `else` branches | 7 branches |
| Repeated mutable objects | List multiplication that can create shared mutable references | No threshold |

The numerical defaults are defined in [`constants.py`](constants.py). They can be overridden for an individual command without editing the source code.

## Requirements

- Python 3.10 or newer
- `pytest` for running the tests

No third-party package is needed to run the checker itself.

## Usage

Analyze a Python file by passing its path as the positional argument:

```powershell
python main.py example.py
```

Paths to files in other directories are also accepted:

```powershell
python main.py src/package/module.py
```

Display the complete command-line help:

```powershell
python main.py --help
```

### Command-line options

```text
usage: main.py [-h] [--max-function-length LINES] [--max-parameters COUNT]
               [--max-nesting DEPTH] [--max-branches COUNT]
               path
```

| Argument | Description | Default |
| --- | --- | ---: |
| `path` | Path to the Python file to analyze | Required |
| `--max-function-length LINES` | Maximum allowed number of lines in a function | 20 |
| `--max-parameters COUNT` | Maximum allowed number of function parameters | 5 |
| `--max-nesting DEPTH` | Maximum allowed nesting depth | 5 |
| `--max-branches COUNT` | Maximum allowed number of `elif`/`else` branches | 7 |

Limits must be non-negative integers. Options may be combined and may appear before or after the file path.

Examples:

```powershell
python main.py example.py --max-function-length 30
python main.py example.py --max-parameters 8 --max-nesting 6
python main.py --max-branches 10 example.py
```

Overrides apply only to that invocation. Running the command again without an option uses the value from `constants.py`.

## Example diagnostics

Given this file:

```python
def calculate(a, b, c, d, e, f):
    return a + b
```

The checker can produce output such as:

```text
example.py: Line 1: Function 'calculate' is missing a docstring.
example.py: Line 1: Function 'calculate' has 6 parameters which exceeds the limit of 5
```

When no checker reports an issue, the CLI prints:

```text
No issues found in example.py.
```

## Shared-reference detection

Multiplying a list that contains a mutable object repeats references to the same object rather than creating independent copies:

```python
grid = [[0] * 3] * 3
```

All three rows in `grid` refer to the same inner list. Changing one row can unexpectedly change every row.

The checker reports:

```text
example.py: Line 1: Repeating a mutable object with '*' creates shared references; use a comprehension instead.
```

Use a comprehension to create each row independently:

```python
grid = [[0] * 3 for _ in range(3)]
```

The rule recognizes obviously mutable expressions, including:

- List, dictionary, and set literals
- List, dictionary, and set comprehensions
- Direct calls to `list()`, `dict()`, `set()`, and `bytearray()`
- List-producing multiplication
- Tuples containing a recognized mutable object

It deliberately does not perform type inference. Names, attributes, subscripts, and arbitrary function calls are treated as unknown.

## Error handling

Missing files are reported cleanly:

```text
Could not find the file: missing.py
```

Syntax errors include the filename and line number:

```text
invalid.py:3: invalid syntax
```

File and syntax errors are written to standard error. Style diagnostics and the no-issues message are written to standard output.

### Exit statuses

| Status | Meaning |
| ---: | --- |
| `0` | The file was analyzed successfully, even if code-quality warnings were found |
| `1` | The file could not be read or parsed |
| `2` | The command-line arguments were invalid |

## How it works

The CLI follows this sequence:

1. `argparse` validates the path and optional limit overrides.
2. `pathlib.Path.read_text()` reads the source using UTF-8.
3. `ast.parse()` creates one `ast.Module` tree.
4. Every checker analyzes that shared tree.
5. The output functions format and print the returned diagnostics.
6. If every result list is empty, the CLI prints the no-issues message.

The analyzed source is never executed.

## Project structure

```text
.
├── main.py             # Command-line parsing, file handling, and orchestration
├── checker.py          # AST-based code-quality checks
├── output_messages.py  # Diagnostic formatting and output
├── constants.py        # Default numerical limits
├── test_checker.py     # Pytest unit and CLI integration tests
└── README.md            # Project documentation
```

## Running the tests

Install the development dependency if necessary:

```powershell
python -m pip install pytest
```

Run the complete suite from the project root:

```powershell
python -m pytest -q
```

The tests cover warning cases, safe cases, exact numerical boundaries, multiple violations, error-resistant AST behavior, and CLI integration.

## Scope and limitations

- This is a syntax-based checker, not a full type analyzer.
- It analyzes one file per command and does not recursively scan directories.
- It does not resolve imports or inspect runtime values.
- The existing function checks analyze regular `def` declarations.
- Nesting currently considers `if`, `for`, and `while` nodes.
- The repeated-mutable-object rule reports only expressions that are obviously mutable from their syntax.

These constraints keep the tool predictable and prevent it from executing untrusted source files.
