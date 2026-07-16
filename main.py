import argparse
import ast
import sys
from pathlib import Path

import checker
import constants
import output_messages


def non_negative_integer(value: str) -> int:
    """Convert a command-line value to a non-negative integer."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error

    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")

    return number


def main(argv: list[str] | None = None) -> int:
    """Analyze one Python file and print any issues that are found."""
    parser = argparse.ArgumentParser(
        description="Analyze a Python file for common code-quality issues.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "path",
        type=Path,
        help="path to the Python file to analyze",
    )
    parser.add_argument(
        "--max-function-length",
        type=non_negative_integer,
        default=constants.MAX_FUNCTION_LENGTH,
        metavar="LINES",
        help="maximum allowed number of lines in a function",
    )
    parser.add_argument(
        "--max-parameters",
        type=non_negative_integer,
        default=constants.MAX_PARAMETER_COUNT,
        metavar="COUNT",
        help="maximum allowed number of function parameters",
    )
    parser.add_argument(
        "--max-nesting",
        type=non_negative_integer,
        default=constants.MAX_NEST_COUNT,
        metavar="DEPTH",
        help="maximum allowed nesting depth",
    )
    parser.add_argument(
        "--max-branches",
        type=non_negative_integer,
        default=constants.MAX_BRANCH_COUNT,
        metavar="COUNT",
        help="maximum allowed number of elif/else branches",
    )
    args = parser.parse_args(argv)
    path = args.path

    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Could not find the file: {path}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Could not read the file {path}: {error}", file=sys.stderr)
        return 1

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        print(f"{error.filename}:{error.lineno}: {error.msg}", file=sys.stderr)
        return 1

    missing_docstrings = checker.check_missing_docstrings(tree)
    long_functions = checker.check_function_length(
        tree, args.max_function_length
    )
    excessive_parameters = checker.check_num_parameters(
        tree, args.max_parameters
    )
    bare_excepts = checker.check_bare_except(tree)
    none_equalities = checker.check_none_equality(tree)
    excessive_nesting = checker.check_excessive_nesting(
        tree, args.max_nesting
    )
    excessive_branches = checker.check_excessive_branches(
        tree, args.max_branches
    )
    repeated_mutable_objects = checker.check_repeated_mutable_objects(tree)

    output_messages.output_missing_docstring_error(path, missing_docstrings)
    output_messages.output_length_error(
        path, long_functions, args.max_function_length
    )
    output_messages.output_max_params_error(
        path, excessive_parameters, args.max_parameters
    )
    output_messages.output_bare_except_error(path, bare_excepts)
    output_messages.output_none_equality_error(path, none_equalities)
    output_messages.output_excessive_nesting_error(
        path, excessive_nesting, args.max_nesting
    )
    output_messages.output_excessive_branches_error(
        path, excessive_branches, args.max_branches
    )
    output_messages.output_repeated_mutable_objects_error(
        path, repeated_mutable_objects
    )

    issues = (
        missing_docstrings,
        long_functions,
        excessive_parameters,
        bare_excepts,
        none_equalities,
        excessive_nesting,
        excessive_branches,
        repeated_mutable_objects,
    )
    if not any(issues):
        print(f"No issues found in {path}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
