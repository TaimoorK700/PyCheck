import ast


_MUTABLE_CONSTRUCTOR_NAMES = {"list", "dict", "set"}
_MUTABLE_EXPRESSION_TYPES = (
    ast.List,
    ast.Dict,
    ast.Set,
    ast.ListComp,
    ast.DictComp,
    ast.SetComp
)


def _is_direct_call_to(expression: ast.expr, names: set[str]) -> bool:
    """Return whether expression directly calls one of the named functions."""
    return (
        isinstance(expression, ast.Call)
        and isinstance(expression.func, ast.Name)
        and expression.func.id in names
    )


def _produces_list(expression: ast.expr) -> bool:
    """Return whether expression obviously produces a list without inference."""
    if isinstance(expression, (ast.List, ast.ListComp)):
        return True

    if _is_direct_call_to(expression, {"list"}):
        return True

    return (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Mult)
        and (
            _produces_list(expression.left)
            or _produces_list(expression.right)
        )
    )


def _creates_obviously_mutable_object(expression: ast.expr) -> bool:
    """Return whether expression directly creates a recognized mutable object."""
    if isinstance(expression, _MUTABLE_EXPRESSION_TYPES):
        return True

    if _is_direct_call_to(expression, _MUTABLE_CONSTRUCTOR_NAMES):
        return True

    if isinstance(expression, ast.Tuple):
        return any(
            _creates_obviously_mutable_object(element)
            for element in expression.elts
        )

    return (
        isinstance(expression, ast.BinOp)
        and isinstance(expression.op, ast.Mult)
        and (
            _produces_list(expression.left)
            or _produces_list(expression.right)
        )
    )


def _integer_literal_value(expression: ast.expr) -> int | None:
    """Return a known integer literal value, including unary signs."""
    if isinstance(expression, ast.Constant) and isinstance(expression.value, int):
        return expression.value

    if (
        isinstance(expression, ast.UnaryOp)
        and isinstance(expression.op, (ast.UAdd, ast.USub))
    ):
        operand = _integer_literal_value(expression.operand)
        if operand is not None:
            return -operand if isinstance(expression.op, ast.USub) else operand

    return None


def _could_repeat_more_than_once(multiplier: ast.expr) -> bool:
    """Return whether multiplier is unknown or a known integer above one."""
    value = _integer_literal_value(multiplier)
    return value is None or value > 1

def check_missing_docstrings(tree: ast.Module) -> list[tuple[int, str]]:
    """Return the line number and name of every function missing a docstring."""
    missing = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if ast.get_docstring(node) is None:
                missing.append((node.lineno, node.name))

    return missing

def check_function_length(tree: ast.Module, max_length: int) -> list[tuple[int, str, int]]:
    """Return the line number, name and length of every function longer than max_length."""
    long_functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.end_lineno is not None:
                function_length = node.end_lineno - node.lineno + 1

                if function_length > max_length:
                    long_functions.append((node.lineno, node.name, function_length))

    return long_functions

def check_num_parameters(tree: ast.Module, max_param_num: int) -> list[tuple[int, str, int]]:
    """Return the line number, name and number of parameters of every function that has more parameters than max_param_num."""
    more_params = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            num_of_params = len(node.args.args)

            if num_of_params > max_param_num:
                more_params.append((node.lineno, node.name, num_of_params))

    return more_params

def check_bare_except(tree: ast.Module) -> list[int]:
    """Return the line numbers which have a bare except statement."""
    bare_except = []

    for node in ast.walk(tree):
        if isinstance(node, ast.excepthandler):
            if node.type is None:
                bare_except.append(node.lineno)

    return bare_except

def check_none_equality(tree: ast.Module) -> list[tuple[int, str]]:
    """Return the line number and operator where None is 
    being compared using == or != instead of 'is'."""
    none_equality = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]

            for left, op, right in zip(operands, node.ops, operands[1:]):
                compare_none = (
                    isinstance(left, ast.Constant) and left.value is None
                ) or (
                    isinstance(right, ast.Constant) and right.value is None
                )

                if compare_none and isinstance(op, (ast.Eq, ast.NotEq)):
                    symbol = "==" if isinstance(op, ast.Eq) else "!="
                    none_equality.append((node.lineno, symbol))

    return none_equality

def check_excessive_nesting(tree: ast.Module, max_nest: int) -> list[tuple[int, str, int]]:
    """Return the line number, function name, and degree of nesting of every function that exceeds the maximum nesting limit."""
    excessive_nesting = []

    nesting_nodes = (ast.If, ast.For, ast.While)

    def find_max_depth(node: ast.AST, current_depth: int = 0) -> int:
        """Return the maximum nesting depth below node."""
        if isinstance(node, nesting_nodes):
            current_depth += 1

        deepest = current_depth

        for child in ast.iter_child_nodes(node):
            child_depth = find_max_depth(child, current_depth)
            deepest = max(deepest, child_depth)

        return deepest
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            depth = find_max_depth(node)
            if depth > max_nest:
                excessive_nesting.append((node.lineno, node.name, depth))

    return excessive_nesting

def check_excessive_branches(tree: ast.Module, max_branches: int) -> list[tuple[int, str, int]]:
    """Return functions whose number of elif/else branches exceeds the limit."""
    excessive_branches = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            branch_count = sum(
                1
                for child in ast.walk(node)
                if isinstance(child, ast.If) and child.orelse
            )

            if branch_count > max_branches:
                excessive_branches.append((node.lineno, node.name, branch_count))

    return excessive_branches


def check_repeated_mutable_objects(tree: ast.Module) -> list[int]:
    """Return lines where list multiplication repeats mutable objects."""
    repeated_mutable_objects = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
            continue

        problematic_left = (
            isinstance(node.left, ast.List)
            and _could_repeat_more_than_once(node.right)
            and any(
                _creates_obviously_mutable_object(element)
                for element in node.left.elts
            )
        )
        problematic_right = (
            isinstance(node.right, ast.List)
            and _could_repeat_more_than_once(node.left)
            and any(
                _creates_obviously_mutable_object(element)
                for element in node.right.elts
            )
        )

        if problematic_left or problematic_right:
            repeated_mutable_objects.append(node.lineno)

    return repeated_mutable_objects

