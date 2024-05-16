import pathlib
from dataclasses import dataclass, field
from typing import List

from codeflash.code_utils.code_extractor import get_code
from codeflash.discovery.functions_to_optimize import FunctionToOptimize
from codeflash.optimization.function_context import (
    get_constrained_function_context_and_dependent_functions,
)


class CustomType:
    def __init__(self) -> None:
        self.name = None
        self.data: List[int] = []


@dataclass
class CustomDataClass:
    name: str = ""
    data: List[int] = field(default_factory=list)


def function_to_optimize(data: CustomType) -> CustomType:
    name = data.name
    data.data.sort()
    return data


def function_to_optimize2(data: CustomDataClass) -> CustomType:
    name = data.name
    data.data.sort()
    return data


def test_function_context_includes_type_annotation() -> None:
    file_path = pathlib.Path(__file__).resolve()
    a, dependent_functions = get_constrained_function_context_and_dependent_functions(
        FunctionToOptimize("function_to_optimize", str(file_path), []),
        str(file_path.parent.resolve()),
        """def function_to_optimize(data: CustomType):
    name = data.name
    data.data.sort()
    return data""",
        1000,
    )

    assert len(dependent_functions) == 1
    assert dependent_functions[0][0].full_name == "CustomType"


def test_function_context_includes_type_annotation_dataclass() -> None:
    file_path = pathlib.Path(__file__).resolve()
    a, dependent_functions = get_constrained_function_context_and_dependent_functions(
        FunctionToOptimize("function_to_optimize2", str(file_path), []),
        str(file_path.parent.resolve()),
        """def function_to_optimize2(data: CustomDataClass) -> CustomType:
    name = data.name
    data.data.sort()
    return data""",
        1000,
    )

    assert len(dependent_functions) == 2
    assert dependent_functions[0][0].full_name == "CustomDataClass"
    assert dependent_functions[1][0].full_name == "CustomType"


def test_function_context_custom_datatype() -> None:
    project_path = pathlib.Path(__file__).parent.parent.resolve() / "code_to_optimize"
    file_path = project_path / "math_utils.py"
    code, contextual_dunder_methods = get_code(
        [FunctionToOptimize("cosine_similarity", str(file_path), [])],
    )
    assert code is not None
    assert contextual_dunder_methods == set()
    a, dependent_functions = get_constrained_function_context_and_dependent_functions(
        FunctionToOptimize("cosine_similarity", str(file_path), []),
        str(project_path),
        code,
        1000,
    )

    assert len(dependent_functions) == 1
    assert dependent_functions[0][0].full_name == "Matrix"
