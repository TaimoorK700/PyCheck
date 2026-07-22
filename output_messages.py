import constants
from pathlib import Path


def output_missing_docstring_error(path: Path, errors: list[tuple[int, str]]) -> None:
    """Print message for missing docstring."""
    for line_number, function_name in errors:
        print(
            f"{path}: Line {line_number}: "
            f"Function '{function_name}' is missing a docstring."
        )

def output_length_error(
    path: Path,
    errors: list[tuple[int, str, int]],
    max_length: int = constants.MAX_FUNCTION_LENGTH,
) -> None:
    """Print message for maximum length exceeded."""
    for line_number, function_name, function_length in errors:
        print(
            f"{path}: Line {line_number}: "
            f"Function '{function_name}' has a length of {function_length} "
            f"which exceeds max length of {max_length}"
        )

def output_max_params_error(
    path: Path,
    errors: list[tuple[int, str, int]],
    max_parameters: int = constants.MAX_PARAMETER_COUNT,
) -> None:
    """Print message for maximum number of parameters exceeded."""
    for line_number, function_name, num_of_params in errors:
        print(
            f"{path}: Line {line_number}: "
            f"Function '{function_name}' has {num_of_params} parameters "
            f"which exceeds the limit of {max_parameters}"
        )

def output_bare_except_error(path: Path, errors: list[int]) -> None:
    """Print message for bare except statement."""
    for line_number in errors:
        print(
            f"{path}: Line {line_number}: "
            f"bare except statement"
        )

def output_none_equality_error(path: Path, errors: list[tuple[int, str]]) -> None:
    """Print message for equality being used to compare NoneType."""
    for line_number, operator in errors:
        replacement = "is" if operator == "==" else "is not"
        print(
            f"{path}: Line {line_number}: "
            f"Use '{replacement} None' instead of '{operator} None'"
        )

def output_excessive_nesting_error(
    path: Path,
    errors: list[tuple[int, str, int]],
    max_nesting: int = constants.MAX_NEST_COUNT,
) -> None:
    """Print message for excessive nesting."""
    for line_number, function_name, nest_degree in errors:
            print(
            f"{path}: Line {line_number}: "
            f"Function '{function_name}' has {nest_degree} degrees of nesting "
            f"which exceeds the limit of {max_nesting}"
        )

def output_excessive_branches_error(
    path: Path,
    errors: list[tuple[int, str, int]],
    max_branches: int = constants.MAX_BRANCH_COUNT,
) -> None:
    """Print messages for functions with too many elif/else branches."""
    for line_number, function_name, branch_count in errors:
        print(
            f"{path}: Line {line_number}: "
            f"Function '{function_name}' has {branch_count} elif/else branches "
            f"which exceeds the limit of {max_branches}"
        )


def output_repeated_mutable_objects_error(path: Path, errors: list[int]) -> None:
    """Print messages for list multiplication that creates shared references."""
    for line_number in errors:
        print(
            f"{path}: Line {line_number}: Repeating a mutable object with '*' "
            "creates shared references; use a comprehension instead."
        )
