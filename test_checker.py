import ast
from pathlib import Path
from textwrap import dedent

import pytest
import checker
import constants
import main as cli

def test_detects_function_without_docstring() -> None:
    """Test that a function without a docstring is reported."""
    source = dedent(
        """\
        def add(x, y):
            return x + y
        """
    )
    tree = ast.parse(source)

    result = checker.check_missing_docstrings(tree)

    assert result == [(1, "add")]

def test_function_with_docstring() -> None:
    """Test that a function with a docstring is not reported."""
    source = dedent(
        '''\
        def add(x, y):
            """Return the sum of x and y."""
            return x + y
        '''
    )
    tree = ast.parse(source)

    result = checker.check_missing_docstrings(tree)

    assert result == []

def test_multiple_functions_without_docstring() -> None:
    """Test that multiple functions without docstrings are reported."""
    source = dedent(
        """\
        def add(x, y):
            return x + y

        def subtract(x, y):
            return x - y
        """
    )
    tree = ast.parse(source)

    result = checker.check_missing_docstrings(tree)

    assert result == [(1, "add"), (4, "subtract")]


def test_reports_function_longer_than_limit() -> None:
    """Test that a function longer than the limit is reported."""
    source = dedent(
        """\
        def add(x, y):
            z = x + y
            x = z - y
            temp = 1 + 1
            return temp + z + x
        """
    )
    tree = ast.parse(source)
    temp_function_limit = 4

    result = checker.check_function_length(tree, temp_function_limit)

    assert result == [(1, 'add', 5)]


def test_allows_function_at_length_limit() -> None:
    """Test that a function exactly at the length limit is not reported."""
    source = dedent(
        """\
        def add(x, y):
            total = x + y
            doubled = total * 2
            return doubled
        """
    )
    tree = ast.parse(source)
    temp_function_limit = 4

    result = checker.check_function_length(tree, temp_function_limit)

    assert result == []


def test_reports_multiple_functions_longer_than_limit() -> None:
    """Test that multiple functions longer than the limit are reported."""
    source = dedent(
        """\
        def add(x, y):
            total = x + y
            doubled = total * 2
            result = doubled + total
            return result

        def subtract(x, y):
            difference = x - y
            doubled = difference * 2
            result = doubled - difference
            return result
        """
    )
    tree = ast.parse(source)
    temp_function_limit = 4

    result = checker.check_function_length(tree, temp_function_limit)

    assert result == [(1, "add", 5), (7, "subtract", 5)]


def test_reports_function_above_parameter_limit() -> None:
    """Test that a function above the parameter limit is reported."""
    source = dedent(
        """\
        def configure(a, b, c, d, e, f):
            return None
        """
    )
    tree = ast.parse(source)

    result = checker.check_num_parameters(tree, constants.MAX_PARAMETER_COUNT)

    assert result == [(1, "configure", 6)]


def test_allows_function_at_parameter_limit() -> None:
    """Test that a function exactly at the parameter limit is not reported."""
    source = dedent(
        """\
        def configure(a, b, c, d, e):
            return None
        """
    )
    tree = ast.parse(source)

    result = checker.check_num_parameters(tree, constants.MAX_PARAMETER_COUNT)

    assert result == []


def test_reports_multiple_functions_above_parameter_limit() -> None:
    """Test that multiple functions above the parameter limit are reported."""
    source = dedent(
        """\
        def first(a, b, c, d, e, f):
            return None

        def second(a, b, c, d, e, f, g):
            return None
        """
    )
    tree = ast.parse(source)

    result = checker.check_num_parameters(tree, constants.MAX_PARAMETER_COUNT)

    assert result == [(1, "first", 6), (4, "second", 7)]


def test_reports_bare_except() -> None:
    """Test that a bare except clause is reported."""
    source = dedent(
        """\
        try:
            risky_operation()
        except:
            pass
        """
    )
    tree = ast.parse(source)

    result = checker.check_bare_except(tree)

    assert result == [3]


def test_allows_typed_except() -> None:
    """Test that an except clause with an exception type is not reported."""
    source = dedent(
        """\
        try:
            risky_operation()
        except ValueError:
            pass
        """
    )
    tree = ast.parse(source)

    result = checker.check_bare_except(tree)

    assert result == []


def test_reports_multiple_bare_excepts() -> None:
    """Test that multiple bare except clauses are reported."""
    source = dedent(
        """\
        try:
            first_operation()
        except:
            pass

        try:
            second_operation()
        except:
            pass
        """
    )
    tree = ast.parse(source)

    result = checker.check_bare_except(tree)

    assert result == [3, 8]


def test_reports_none_equality_comparison() -> None:
    """Test that comparing None with equality is reported."""
    source = dedent(
        """\
        if value == None:
            handle_missing_value()
        """
    )
    tree = ast.parse(source)

    result = checker.check_none_equality(tree)

    assert result == [(1, "==")]


def test_allows_none_identity_comparison() -> None:
    """Test that comparing None with identity is not reported."""
    source = dedent(
        """\
        if value is None:
            handle_missing_value()
        """
    )
    tree = ast.parse(source)

    result = checker.check_none_equality(tree)

    assert result == []


def test_reports_multiple_none_equality_comparisons() -> None:
    """Test that multiple invalid None comparisons are reported."""
    source = dedent(
        """\
        if first == None:
            handle_first()

        if None != second:
            handle_second()
        """
    )
    tree = ast.parse(source)

    result = checker.check_none_equality(tree)

    assert result == [(1, "=="), (4, "!=")]


def test_reports_nesting_above_limit() -> None:
    """Test that nesting above the maximum depth is reported."""
    source = dedent(
        """\
        def process(value):
            if value:
                while value > 0:
                    for item in range(value):
                        print(item)
        """
    )
    tree = ast.parse(source)
    temp_nest_limit = 2

    result = checker.check_excessive_nesting(tree, temp_nest_limit)

    assert result == [(1, "process", 3)]


def test_allows_nesting_at_limit() -> None:
    """Test that nesting exactly at the maximum depth is not reported."""
    source = dedent(
        """\
        def process(value):
            if value:
                while value > 0:
                    value -= 1
        """
    )
    tree = ast.parse(source)
    temp_nest_limit = 2

    result = checker.check_excessive_nesting(tree, temp_nest_limit)

    assert result == []


def test_reports_multiple_functions_above_nesting_limit() -> None:
    """Test that multiple excessively nested functions are reported."""
    source = dedent(
        """\
        def first(value):
            if value:
                while value > 0:
                    for item in range(value):
                        print(item)

        def second(items):
            for item in items:
                if item:
                    while item:
                        item -= 1
        """
    )
    tree = ast.parse(source)
    temp_nest_limit = 2

    result = checker.check_excessive_nesting(tree, temp_nest_limit)

    assert result == [(1, "first", 3), (7, "second", 3)]


def test_reports_branch_count_above_limit() -> None:
    """Test that an elif/else branch count above the limit is reported."""
    source = dedent(
        """\
        def categorize(value):
            if value < 0:
                return "negative"
            elif value == 0:
                return "zero"
            elif value == 1:
                return "one"
            else:
                return "positive"
        """
    )
    tree = ast.parse(source)
    temp_branch_limit = 2

    result = checker.check_excessive_branches(tree, temp_branch_limit)

    assert result == [(1, "categorize", 3)]


def test_allows_branch_count_at_limit() -> None:
    """Test that an elif/else branch count at the limit is not reported."""
    source = dedent(
        """\
        def categorize(value):
            if value < 0:
                return "negative"
            elif value == 0:
                return "zero"
            else:
                return "positive"
        """
    )
    tree = ast.parse(source)
    temp_branch_limit = 2

    result = checker.check_excessive_branches(tree, temp_branch_limit)

    assert result == []


def test_reports_multiple_functions_above_branch_limit() -> None:
    """Test that multiple functions with too many branches are reported."""
    source = dedent(
        """\
        def first(value):
            if value < 0:
                return "negative"
            elif value == 0:
                return "zero"
            elif value == 1:
                return "one"
            else:
                return "positive"

        def second(value):
            if value < 0:
                return "low"
            elif value == 0:
                return "middle"
            elif value == 1:
                return "high"
            else:
                return "other"
        """
    )
    tree = ast.parse(source)
    temp_branch_limit = 2

    result = checker.check_excessive_branches(tree, temp_branch_limit)

    assert result == [(1, "first", 3), (11, "second", 3)]


def test_reports_repeated_list_literal() -> None:
    """Test that repeating a nested list literal is reported."""
    tree = ast.parse("items = [[]] * 3")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


def test_reports_repeated_dictionary_literal() -> None:
    """Test that repeating a dictionary literal is reported."""
    tree = ast.parse("items = [{}] * 2")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


def test_reports_repeated_set_literal() -> None:
    """Test that repeating a set literal is reported."""
    tree = ast.parse("items = [{1, 2}] * 2")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


def test_reports_repeated_list_producing_multiplication() -> None:
    """Test that a repeated list multiplication result is reported."""
    tree = ast.parse("grid = [[0] * 3] * 3")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


def test_reports_repeated_mutable_object_with_reversed_operands() -> None:
    """Test that multiplication with the list on the right is reported."""
    tree = ast.parse("items = 3 * [[]]")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


@pytest.mark.parametrize(
    "constructor",
    ["list()", "dict()", "set()"],
)
def test_reports_repeated_mutable_constructor_call(constructor: str) -> None:
    """Test that direct calls creating mutable objects are reported."""
    tree = ast.parse(f"items = [{constructor}] * 3")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


@pytest.mark.parametrize(
    "comprehension",
    [
        "[value for value in values]",
        "{value: value for value in values}",
        "{value for value in values}",
    ],
)
def test_reports_repeated_mutable_comprehension(comprehension: str) -> None:
    """Test that list, dictionary, and set comprehensions are recognized."""
    tree = ast.parse(f"items = [{comprehension}] * 3")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


def test_reports_repeated_tuple_containing_mutable_object() -> None:
    """Test that a tuple containing a mutable object is recognized."""
    tree = ast.parse("items = [([],)] * 3")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


def test_reports_multiple_repeated_mutable_objects() -> None:
    """Test that multiple problematic expressions return their line numbers."""
    source = dedent(
        """\
        first = [[]] * 3
        safe = [0] * 3
        second = 2 * [{}]
        third = [set()] * count
        """
    )
    tree = ast.parse(source)

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1, 3, 4]


@pytest.mark.parametrize(
    "element",
    [
        "0",
        '"x"',
        "None",
        "(1, 2)",
        "len([])",
        "name",
        "factory()",
        "obj.value",
        "items[0]",
    ],
)
def test_allows_repeated_unknown_or_immutable_element(element: str) -> None:
    """Test that immutable and unknown element expressions are not reported."""
    tree = ast.parse(f"items = [{element}] * 3")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == []


def test_allows_comprehension_instead_of_outer_list_multiplication() -> None:
    """Test that independently created rows in a comprehension are allowed."""
    tree = ast.parse("grid = [[0] * 3 for _ in range(3)]")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == []


@pytest.mark.parametrize(
    "source",
    [
        "items = [[]] * 0",
        "items = [[]] * 1",
        "items = [[]] * -1",
        "items = -3 * [[]]",
    ],
)
def test_allows_multiplier_that_cannot_repeat_references(source: str) -> None:
    """Test that known integer multipliers below two are allowed."""
    tree = ast.parse(source)

    result = checker.check_repeated_mutable_objects(tree)

    assert result == []


def test_reports_unknown_multiplier() -> None:
    """Test that an unknown multiplier is treated as potentially above one."""
    tree = ast.parse("items = [[]] * count")

    result = checker.check_repeated_mutable_objects(tree)

    assert result == [1]


def test_cli_reports_repeated_mutable_object(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that the CLI prints the shared-reference warning."""
    path = tmp_path / "shared_rows.py"
    path.write_text("grid = [[0] * 3] * 3\n", encoding="utf-8")

    exit_code = cli.main([str(path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        f"{path}: Line 1: Repeating a mutable object with '*' creates shared "
        "references; use a comprehension instead.\n"
    )
    assert "No issues found" not in captured.out
    assert captured.err == ""


if __name__ == '__main__':
    pytest.main()
