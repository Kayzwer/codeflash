from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

from codeflash.code_utils.code_replacer import replace_functions_and_add_imports, replace_functions_in_file
from codeflash.discovery.functions_to_optimize import FunctionParent, FunctionToOptimize
from codeflash.optimization.optimizer import Optimizer

os.environ["CODEFLASH_API_KEY"] = "cf-test-key"


def test_test_libcst_code_replacement() -> None:
    optim_code = """import libcst as cst
from typing import Optional

def totally_new_function(value):
    return value

class NewClass:
    def __init__(self, name):
        self.name = name
    def new_function(self, value):
        return self.name
    def new_function2(value):
        return value
    """

    original_code = """class NewClass:
    def __init__(self, name):
        self.name = name
    def new_function(self, value):
        return "I am still old"

print("Hello world")
"""
    expected = """class NewClass:
    def __init__(self, name):
        self.name = name
    def new_function(self, value):
        return self.name
    def new_function2(value):
        return value

def totally_new_function(value):
    return value

print("Hello world")
"""

    function_name: str = "NewClass.new_function"
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = [
        ("new_function", [FunctionParent(name="NewClass", type="ClassDef")]),
    ]
    contextual_functions: set[tuple[str, str]] = {("NewClass", "__init__")}
    new_code: str = replace_functions_and_add_imports(
        source_code=original_code,
        function_names=[function_name],
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_code == expected


def test_test_libcst_code_replacement2() -> None:
    optim_code = """import libcst as cst
from typing import Optional

def totally_new_function(value):
    return value

def other_function(st):
    return(st * 2)

class NewClass:
    def __init__(self, name):
        self.name = name
    def new_function(self, value):
        return other_function(self.name)
    def new_function2(value):
        return value
    """

    original_code = """from OtherModule import other_function

class NewClass:
    def __init__(self, name):
        self.name = name
    def new_function(self, value):
        return other_function("I am still old")

print("Hello world")
"""
    expected = """from OtherModule import other_function

class NewClass:
    def __init__(self, name):
        self.name = name
    def new_function(self, value):
        return other_function(self.name)
    def new_function2(value):
        return value

def totally_new_function(value):
    return value

print("Hello world")
"""

    function_name: str = "NewClass.new_function"
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = [
        ("new_function", []),
        ("other_function", []),
    ]
    contextual_functions: set[tuple[str, str]] = {("NewClass", "__init__")}
    new_code: str = replace_functions_and_add_imports(
        source_code=original_code,
        function_names=[function_name],
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_code == expected


def test_test_libcst_code_replacement3() -> None:
    optim_code = """import libcst as cst
from typing import Optional

def totally_new_function(value):
    return value

def other_function(st):
    return(st * 2)

class NewClass:
    def __init__(self, name):
        self.name = name
    def new_function(self, value: cst.Name):
        return other_function(self.name)
    def new_function2(value):
        return value
    """

    original_code = """import libcst as cst
from typing import Mandatory

print("Au revoir")

def yet_another_function(values):
    return len(values)

def other_function(st):
    return(st + st)

print("Salut monde")
"""
    expected = """from typing import Mandatory

print("Au revoir")

def yet_another_function(values):
    return len(values)

def other_function(st):
    return(st * 2)

print("Salut monde")
"""

    function_names: list[str] = ["module.other_function"]
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = []
    contextual_functions: set[tuple[str, str]] = set()
    new_code: str = replace_functions_and_add_imports(
        source_code=original_code,
        function_names=function_names,
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_code == expected


def test_test_libcst_code_replacement4() -> None:
    optim_code = """import libcst as cst
from typing import Optional

def totally_new_function(value):
    return value

def yet_another_function(values: Optional[str]):
    return len(values) + 2

def other_function(st):
    return(st * 2)

class NewClass:
    def __init__(self, name):
        self.name = name
    def new_function(self, value):
        return other_function(self.name)
    def new_function2(value):
        return value
    """

    original_code = """import libcst as cst
from typing import Mandatory

print("Au revoir")

def yet_another_function(values):
    return len(values)

def other_function(st):
    return(st + st)

print("Salut monde")
"""
    expected = """from typing import Optional, Mandatory

print("Au revoir")

def yet_another_function(values: Optional[str]):
    return len(values) + 2

def other_function(st):
    return(st * 2)

print("Salut monde")
"""

    function_names: list[str] = ["module.yet_another_function", "module.other_function"]
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = []
    contextual_functions: set[tuple[str, str]] = set()
    new_code: str = replace_functions_and_add_imports(
        source_code=original_code,
        function_names=function_names,
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_code == expected


def test_test_libcst_code_replacement5() -> None:
    optim_code = """def sorter_deps(arr):
    supersort(badsort(arr))
    return arr

def badsort(ploc):
    donothing(ploc)

def supersort(doink):
    for i in range(len(doink)):
        fix(doink, i)
"""

    original_code = """from code_to_optimize.bubble_sort_dep1_helper import dep1_comparer
from code_to_optimize.bubble_sort_dep2_swap import dep2_swap

def sorter_deps(arr):
    for i in range(len(arr)):
        for j in range(len(arr) - 1):
            if dep1_comparer(arr, j):
                dep2_swap(arr, j)
    return arr
"""
    expected = """from code_to_optimize.bubble_sort_dep1_helper import dep1_comparer
from code_to_optimize.bubble_sort_dep2_swap import dep2_swap
def sorter_deps(arr):
    supersort(badsort(arr))
    return arr

def badsort(ploc):
    donothing(ploc)

def supersort(doink):
    for i in range(len(doink)):
        fix(doink, i)
"""

    function_names: list[str] = ["sorter_deps"]
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = [("sorter_deps", [])]
    contextual_functions: set[tuple[str, str]] = set()
    new_code: str = replace_functions_and_add_imports(
        source_code=original_code,
        function_names=function_names,
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_code == expected


def test_test_libcst_code_replacement6() -> None:
    optim_code = """import libcst as cst
from typing import Optional

def other_function(st):
    return(st * blob(st))

def blob(st):
    return(st * 2)
"""
    original_code_main = """import libcst as cst
from typing import Mandatory
from helper import blob

print("Au revoir")

def yet_another_function(values):
    return len(values)

def other_function(st):
    return(st + blob(st))

print("Salut monde")
"""

    original_code_helper = """import numpy as np

print("Cool")

def blob(values):
    return len(values)

def blab(st):
    return(st + st)

print("Not cool")
"""
    expected_main = """from typing import Mandatory
from helper import blob

print("Au revoir")

def yet_another_function(values):
    return len(values)

def other_function(st):
    return(st * blob(st))

print("Salut monde")
"""

    expected_helper = """import numpy as np

print("Cool")

def blob(st):
    return(st * 2)

def blab(st):
    return(st + st)

print("Not cool")
"""
    new_main_code: str = replace_functions_and_add_imports(
        source_code=original_code_main,
        function_names=["other_function"],
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=[("other_function", []), ("yet_another_function", []), ("blob", [])],
        contextual_functions=set(),
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_main_code == expected_main

    new_helper_code: str = replace_functions_and_add_imports(
        source_code=original_code_helper,
        function_names=["blob"],
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=[],
        contextual_functions=set(),
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_helper_code == expected_helper


def test_test_libcst_code_replacement7() -> None:
    optim_code = """@register_deserializable
class CacheSimilarityEvalConfig(BaseConfig):

    def __init__(
        self,
        strategy: Optional[str] = "distance",
        max_distance: Optional[float] = 1.0,
        positive: Optional[bool] = False,
    ):
        self.strategy = strategy
        self.max_distance = max_distance
        self.positive = positive

    @staticmethod
    def from_config(config: Optional[dict[str, Any]]):
        if config is None:
            return CacheSimilarityEvalConfig()

        strategy = config.get("strategy", "distance")
        max_distance = config.get("max_distance", 1.0)
        positive = config.get("positive", False)

        return CacheSimilarityEvalConfig(strategy, max_distance, positive)
"""

    original_code = """from typing import Any, Optional

from embedchain.config.base_config import BaseConfig
from embedchain.helpers.json_serializable import register_deserializable


@register_deserializable
class CacheSimilarityEvalConfig(BaseConfig):

    def __init__(
        self,
        strategy: Optional[str] = "distance",
        max_distance: Optional[float] = 1.0,
        positive: Optional[bool] = False,
    ):
        self.strategy = strategy
        self.max_distance = max_distance
        self.positive = positive

    @staticmethod
    def from_config(config: Optional[dict[str, Any]]):
        if config is None:
            return CacheSimilarityEvalConfig()
        else:
            return CacheSimilarityEvalConfig(
                strategy=config.get("strategy", "distance"),
                max_distance=config.get("max_distance", 1.0),
                positive=config.get("positive", False),
            )


@register_deserializable
class CacheInitConfig(BaseConfig):

    def __init__(
        self,
        similarity_threshold: Optional[float] = 0.8,
        auto_flush: Optional[int] = 20,
    ):
        if similarity_threshold < 0 or similarity_threshold > 1:
            raise ValueError(f"similarity_threshold {similarity_threshold} should be between 0 and 1")

        self.similarity_threshold = similarity_threshold
        self.auto_flush = auto_flush

    @staticmethod
    def from_config(config: Optional[dict[str, Any]]):
        if config is None:
            return CacheInitConfig()
        else:
            return CacheInitConfig(
                similarity_threshold=config.get("similarity_threshold", 0.8),
                auto_flush=config.get("auto_flush", 20),
            )


@register_deserializable
class CacheConfig(BaseConfig):

    def __init__(
        self,
        similarity_eval_config: Optional[CacheSimilarityEvalConfig] = CacheSimilarityEvalConfig(),
        init_config: Optional[CacheInitConfig] = CacheInitConfig(),
    ):
        self.similarity_eval_config = similarity_eval_config
        self.init_config = init_config

    @staticmethod
    def from_config(config: Optional[dict[str, Any]]):
        if config is None:
            return CacheConfig()
        else:
            return CacheConfig(
                similarity_eval_config=CacheSimilarityEvalConfig.from_config(config.get("similarity_evaluation", {})),
                init_config=CacheInitConfig.from_config(config.get("init_config", {})),
            )
"""
    expected = """from typing import Any, Optional

from embedchain.config.base_config import BaseConfig
from embedchain.helpers.json_serializable import register_deserializable


@register_deserializable
class CacheSimilarityEvalConfig(BaseConfig):

    def __init__(
        self,
        strategy: Optional[str] = "distance",
        max_distance: Optional[float] = 1.0,
        positive: Optional[bool] = False,
    ):
        self.strategy = strategy
        self.max_distance = max_distance
        self.positive = positive

    @staticmethod
    def from_config(config: Optional[dict[str, Any]]):
        if config is None:
            return CacheSimilarityEvalConfig()

        strategy = config.get("strategy", "distance")
        max_distance = config.get("max_distance", 1.0)
        positive = config.get("positive", False)

        return CacheSimilarityEvalConfig(strategy, max_distance, positive)


@register_deserializable
class CacheInitConfig(BaseConfig):

    def __init__(
        self,
        similarity_threshold: Optional[float] = 0.8,
        auto_flush: Optional[int] = 20,
    ):
        if similarity_threshold < 0 or similarity_threshold > 1:
            raise ValueError(f"similarity_threshold {similarity_threshold} should be between 0 and 1")

        self.similarity_threshold = similarity_threshold
        self.auto_flush = auto_flush

    @staticmethod
    def from_config(config: Optional[dict[str, Any]]):
        if config is None:
            return CacheInitConfig()
        else:
            return CacheInitConfig(
                similarity_threshold=config.get("similarity_threshold", 0.8),
                auto_flush=config.get("auto_flush", 20),
            )


@register_deserializable
class CacheConfig(BaseConfig):

    def __init__(
        self,
        similarity_eval_config: Optional[CacheSimilarityEvalConfig] = CacheSimilarityEvalConfig(),
        init_config: Optional[CacheInitConfig] = CacheInitConfig(),
    ):
        self.similarity_eval_config = similarity_eval_config
        self.init_config = init_config

    @staticmethod
    def from_config(config: Optional[dict[str, Any]]):
        if config is None:
            return CacheConfig()
        else:
            return CacheConfig(
                similarity_eval_config=CacheSimilarityEvalConfig.from_config(config.get("similarity_evaluation", {})),
                init_config=CacheInitConfig.from_config(config.get("init_config", {})),
            )
"""
    function_names: list[str] = ["CacheSimilarityEvalConfig.from_config"]
    parents = [FunctionParent(name="CacheConfig", type="ClassDef")]
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = [
        ("__init__", parents),
        ("from_config", parents),
    ]

    contextual_functions: set[tuple[str, str]] = {
        ("CacheSimilarityEvalConfig", "__init__"),
        ("CacheConfig", "__init__"),
        ("CacheInitConfig", "__init__"),
    }
    new_code: str = replace_functions_and_add_imports(
        source_code=original_code,
        function_names=function_names,
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_code == expected


def test_test_libcst_code_replacement8() -> None:
    optim_code = '''class _EmbeddingDistanceChainMixin(Chain):
    @staticmethod
    def _hamming_distance(a: np.ndarray, b: np.ndarray) -> np.floating:
        """Compute the Hamming distance between two vectors.

        Args:
            a (np.ndarray): The first vector.
            b (np.ndarray): The second vector.

        Returns:
            np.floating: The Hamming distance.
        """
        return np.sum(a != b) / a.size
'''

    original_code = '''class _EmbeddingDistanceChainMixin(Chain):

    class Config:
        """Permit embeddings to go unvalidated."""

        arbitrary_types_allowed: bool = True


    @staticmethod
    def _hamming_distance(a: np.ndarray, b: np.ndarray) -> np.floating:
        """Compute the Hamming distance between two vectors.

        Args:
            a (np.ndarray): The first vector.
            b (np.ndarray): The second vector.

        Returns:
            np.floating: The Hamming distance.
        """
        return np.mean(a != b)
'''
    expected = '''class _EmbeddingDistanceChainMixin(Chain):

    class Config:
        """Permit embeddings to go unvalidated."""

        arbitrary_types_allowed: bool = True
    @staticmethod
    def _hamming_distance(a: np.ndarray, b: np.ndarray) -> np.floating:
        """Compute the Hamming distance between two vectors.

        Args:
            a (np.ndarray): The first vector.
            b (np.ndarray): The second vector.

        Returns:
            np.floating: The Hamming distance.
        """
        return np.sum(a != b) / a.size
'''
    function_names: list[str] = ["_EmbeddingDistanceChainMixin._hamming_distance"]
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = [
        ("_hamming_distance", [FunctionParent("_EmbeddingDistanceChainMixin", "ClassDef")]),
    ]
    contextual_functions: set[tuple[str, str]] = set()
    new_code: str = replace_functions_and_add_imports(
        source_code=original_code,
        function_names=function_names,
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_code == expected


def test_test_libcst_code_replacement9() -> None:
    optim_code = """import libcst as cst
from typing import Optional

def totally_new_function(value: Optional[str]):
    return value

class NewClass:
    def __init__(self, name):
        self.name = str(name)
    def __call__(self, value):
        return self.name
    def new_function2(value):
        return cst.ensure_type(value, str)
    """

    original_code = """class NewClass:
    def __init__(self, name):
        self.name = name
    def __call__(self, value):
        return "I am still old"

print("Hello world")
"""
    expected = """import libcst as cst
from typing import Optional

class NewClass:
    def __init__(self, name):
        self.name = str(name)
    def __call__(self, value):
        return "I am still old"
    def new_function2(value):
        return cst.ensure_type(value, str)

def totally_new_function(value: Optional[str]):
    return value

print("Hello world")
"""
    parents = [FunctionParent(name="NewClass", type="ClassDef")]
    function_name: str = "NewClass.__init__"
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = [
        ("__init__", parents),
        ("__call__", parents),
    ]
    contextual_functions: set[tuple[str, str]] = {
        ("NewClass", "__init__"),
        ("NewClass", "__call__"),
    }
    new_code: str = replace_functions_and_add_imports(
        source_code=original_code,
        function_names=[function_name],
        optimized_code=optim_code,
        file_path_of_module_with_function_to_optimize=str(Path(__file__).resolve()),
        module_abspath=str(Path(__file__).resolve()),
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
        project_root_path=str(Path(__file__).resolve().parent.resolve()),
    )
    assert new_code == expected


class HelperClass:
    def __init__(self, name):
        self.name = name

    def innocent_bystander(self):
        pass

    def helper_method(self):
        return self.name


class MainClass:
    def __init__(self, name):
        self.name = name

    def main_method(self):
        return HelperClass(self.name).helper_method()


def test_code_replacement10() -> None:
    get_code_output = """from __future__ import annotations

class HelperClass:
    def __init__(self, name):
        self.name = name

    def innocent_bystander(self):
        pass

    def helper_method(self):
        return self.name

class MainClass:
    def __init__(self, name):
        self.name = name
    def main_method(self):
        return HelperClass(self.name).helper_method()
"""
    file_path = Path(__file__).resolve()
    opt = Optimizer(
        Namespace(
            project_root=str(file_path.parent.resolve()),
            disable_telemetry=True,
            tests_root="tests",
            test_framework="pytest",
            pytest_cmd="pytest",
            experiment_id=None,
        ),
    )
    func_top_optimize = FunctionToOptimize(
        function_name="main_method",
        file_path=str(file_path),
        parents=[FunctionParent("MainClass", "ClassDef")],
    )
    with open(file_path) as f:
        original_code = f.read()
        code_context = opt.get_code_optimization_context(
            function_to_optimize=func_top_optimize,
            project_root=str(file_path.parent),
            original_source_code=original_code,
        ).unwrap()
        assert code_context.code_to_optimize_with_helpers == get_code_output


def test_code_replacement11() -> None:
    optim_code = '''class Fu():
    def foo(self) -> dict[str, str]:
        payload: dict[str, str] = {"bar": self.bar(), "real_bar": str(self.real_bar() + 1)}
        return payload

    def real_bar(self) -> int:
        """No abstract nonsense"""
        pass
'''
    original_code = '''class Fu():
    def foo(self) -> dict[str, str]:
        payload: dict[str, str] = {"bar": self.bar(), "real_bar": str(self.real_bar())}
        return payload

    def real_bar(self) -> int:
        """No abstract nonsense"""
        return 0
'''
    expected_code = '''class Fu():
    def foo(self) -> dict[str, str]:
        payload: dict[str, str] = {"bar": self.bar(), "real_bar": str(self.real_bar() + 1)}
        return payload

    def real_bar(self) -> int:
        """No abstract nonsense"""
        return 0
'''

    function_name: str = "Fu.foo"
    parents = [FunctionParent("Fu", "ClassDef")]
    preexisting_functions: list[tuple[str, list[FunctionParent]]] = [("foo", parents), ("real_bar", parents)]
    contextual_functions: set[tuple[str, str]] = set()
    new_code: str = replace_functions_in_file(
        source_code=original_code,
        original_function_names=[function_name],
        optimized_code=optim_code,
        preexisting_functions=preexisting_functions,
        contextual_functions=contextual_functions,
    )
    assert new_code == expected_code
