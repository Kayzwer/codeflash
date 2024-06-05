from __future__ import annotations

import ast
import os.path
import pathlib
import sys
import tempfile

import pytest

from codeflash.code_utils.code_utils import get_run_tmp_file
from codeflash.code_utils.config_consts import INDIVIDUAL_TESTCASE_TIMEOUT
from codeflash.code_utils.instrument_existing_tests import (
    FunctionImportedAsVisitor,
    InjectPerfOnly,
    inject_profiling_into_existing_test,
)
from codeflash.verification.parse_test_output import parse_test_results
from codeflash.verification.test_results import TestType
from codeflash.verification.test_runner import run_tests
from codeflash.verification.verification_utils import TestConfig


def test_perfinjector_bubble_sort() -> None:
    code = """import unittest

from code_to_optimize.bubble_sort import sorter


class TestPigLatin(unittest.TestCase):
    def test_sort(self):
        input = [5, 4, 3, 2, 1, 0]
        output = sorter(input)
        self.assertEqual(output, [0, 1, 2, 3, 4, 5])

        input = [5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
        output = sorter(input)
        self.assertEqual(output, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])

        input = list(reversed(range(5000)))
        output = sorter(input)
        self.assertEqual(output, list(range(5000)))
"""
    expected = """import gc
import os
import sqlite3
import time
import unittest

import dill as pickle
import timeout_decorator

from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    """
    if sys.version_info < (3, 12):
        expected += """print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")"""
    else:
        expected += """print(f'!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!')"""
    expected += """
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

class TestPigLatin(unittest.TestCase):

    @timeout_decorator.timeout(15)
    def test_sort(self):
        codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
        codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
        codeflash_cur = codeflash_con.cursor()
        codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
        input = [5, 4, 3, 2, 1, 0]
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '5', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        self.assertEqual(output, [0, 1, 2, 3, 4, 5])
        input = [5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '8', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        self.assertEqual(output, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        input = list(reversed(range(5000)))
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '11', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        self.assertEqual(output, list(range(5000)))
        codeflash_con.close()
"""
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(code)
        f.flush()
        success, new_test = inject_profiling_into_existing_test(
            f.name, "sorter", os.path.dirname(f.name), "unittest"
        )
    assert success
    assert new_test == expected.format(
        module_path=os.path.basename(f.name),
        tmp_dir_path=get_run_tmp_file("test_return_values"),
    )


def test_perfinjector_only_replay_test() -> None:
    code = """import dill as pickle
import pytest
from codeflash.tracing.replay_test import get_next_arg_and_return
from codeflash.validation.equivalence import compare_results
from packagename.ml.yolo.image_reshaping_utils import prepare_image_for_yolo as packagename_ml_yolo_image_reshaping_utils_prepare_image_for_yolo
def test_prepare_image_for_yolo():
    for arg_val_pkl, return_val_pkl in get_next_arg_and_return('/home/saurabh/packagename/traces/first.trace', 3):
        args = pickle.loads(arg_val_pkl)
        return_val_1= pickle.loads(return_val_pkl)
        ret = packagename_ml_yolo_image_reshaping_utils_prepare_image_for_yolo(**args)
        assert compare_results(return_val_1, ret)
"""
    expected = """import gc
import os
import sqlite3
import time

import dill as pickle
import pytest
from packagename.ml.yolo.image_reshaping_utils import \\
    prepare_image_for_yolo as \\
    packagename_ml_yolo_image_reshaping_utils_prepare_image_for_yolo

from codeflash.tracing.replay_test import get_next_arg_and_return
from codeflash.validation.equivalence import compare_results


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    """
    if sys.version_info < (3, 12):
        expected += """print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")"""
    else:
        expected += """print(f'!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!')"""
    expected += """
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

def test_prepare_image_for_yolo():
    codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
    codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
    codeflash_cur = codeflash_con.cursor()
    codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
"""
    if sys.version_info < (3, 11):
        expected += """    for (arg_val_pkl, return_val_pkl) in get_next_arg_and_return('/home/saurabh/packagename/traces/first.trace', 3):
"""
    else:
        expected += """    for arg_val_pkl, return_val_pkl in get_next_arg_and_return('/home/saurabh/packagename/traces/first.trace', 3):
"""
    expected += """        args = pickle.loads(arg_val_pkl)
        return_val_1 = pickle.loads(return_val_pkl)
        codeflash_return_value = codeflash_wrap(packagename_ml_yolo_image_reshaping_utils_prepare_image_for_yolo, '{module_path}', None, 'test_prepare_image_for_yolo', 'packagename_ml_yolo_image_reshaping_utils_prepare_image_for_yolo', '4_2', codeflash_cur, codeflash_con, **args)
        ret = codeflash_return_value
        assert compare_results(return_val_1, ret)
    codeflash_con.close()
"""
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(code)
        f.flush()

        success, new_test = inject_profiling_into_existing_test(
            f.name,
            "prepare_image_for_yolo",
            os.path.dirname(f.name),
            pytest,
        )
    assert success
    assert new_test == expected.format(
        module_path=os.path.basename(f.name),
        tmp_dir_path=get_run_tmp_file("test_return_values"),
    )


def test_perfinjector_bubble_sort_results() -> None:
    code = """from code_to_optimize.bubble_sort import sorter


def test_sort():
    input = [5, 4, 3, 2, 1, 0]
    output = sorter(input)
    assert output == [0, 1, 2, 3, 4, 5]

    input = [5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
    output = sorter(input)
    assert output == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]"""

    expected = """import gc
import os
import sqlite3
import time

import dill as pickle
import timeout_decorator

from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

def test_sort():
    codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
    codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
    codeflash_cur = codeflash_con.cursor()
    codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
    input = [5, 4, 3, 2, 1, 0]
    codeflash_return_value = codeflash_wrap(sorter, '{module_path}', None, 'test_sort', 'sorter', '5', codeflash_cur, codeflash_con, input)
    output = codeflash_return_value
    assert output == [0, 1, 2, 3, 4, 5]
    input = [5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
    codeflash_return_value = codeflash_wrap(sorter, '{module_path}', None, 'test_sort', 'sorter', '8', codeflash_cur, codeflash_con, input)
    output = codeflash_return_value
    assert output == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/pytest/test_perfinjector_bubble_sort_results_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/pytest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "sorter", project_root_path, "pytest"
        )
        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.pytest.test_perfinjector_bubble_sort_results_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")

        # Overwrite old test with new instrumented test
        with open(test_path, "w") as f:
            f.write(new_test)

        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = "0"
        test_type = TestType.EXISTING_UNIT_TEST
        test_cfg = TestConfig(
            tests_root=str(tests_root),
            project_root_path=str(project_root_path),
            test_framework="pytest",
            pytest_cmd="pytest",
        )
        result_file_path, run_result = run_tests(
            str(test_path),
            test_framework="pytest",
            cwd=str(project_root_path),
            pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
            pytest_cmd="pytest",
            verbose=True,
            test_env=test_env,
        )
        test_results = parse_test_results(
            test_xml_path=result_file_path,
            test_py_path=str(test_path),
            test_config=test_cfg,
            test_type=test_type,
            run_result=run_result,
            optimization_iteration=0,
        )
        assert test_results[0].id.function_getting_tested == "sorter"
        assert test_results[0].id.iteration_id == "5_0"
        assert test_results[0].id.test_class_name is None
        assert test_results[0].id.test_function_name == "test_sort"
        assert (
            test_results[0].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_results_temp"
        )
        assert test_results[0].runtime > 0
        assert test_results[0].did_pass

        assert test_results[1].id.function_getting_tested == "sorter"
        assert test_results[1].id.iteration_id == "8_0"
        assert test_results[1].id.test_class_name is None
        assert test_results[1].id.test_function_name == "test_sort"
        assert (
            test_results[1].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_results_temp"
        )
        assert test_results[1].runtime > 0
        assert test_results[1].did_pass
    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)


def test_perfinjector_bubble_sort_parametrized_results() -> None:
    code = """from code_to_optimize.bubble_sort import sorter
import pytest


@pytest.mark.parametrize(
    "input, expected_output",
    [
        ([5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5]),
        ([5.0, 4.0, 3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]),
        (list(reversed(range(50))), list(range(50))),
    ],
)
def test_sort_parametrized(input, expected_output):
    output = sorter(input)
    assert output == expected_output
"""
    expected = """import gc
import os
import sqlite3
import time

import dill as pickle
import pytest
import timeout_decorator

from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

@pytest.mark.parametrize('input, expected_output', [([5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5]), ([5.0, 4.0, 3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]), (list(reversed(range(50))), list(range(50)))])
def test_sort_parametrized(input, expected_output):
    codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
    codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
    codeflash_cur = codeflash_con.cursor()
    codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
    codeflash_return_value = codeflash_wrap(sorter, '{module_path}', None, 'test_sort_parametrized', 'sorter', '4', codeflash_cur, codeflash_con, input)
    output = codeflash_return_value
    assert output == expected_output
    codeflash_con.close()
"""
    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/pytest/test_perfinjector_bubble_sort_parametrized_results_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/pytest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "sorter", project_root_path, "pytest"
        )
        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.pytest.test_perfinjector_bubble_sort_parametrized_results_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")

        # Overwrite old test with new instrumented test
        with open(test_path, "w") as f:
            f.write(new_test)

        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = "0"
        test_type = TestType.EXISTING_UNIT_TEST
        test_cfg = TestConfig(
            tests_root=str(tests_root),
            project_root_path=str(project_root_path),
            test_framework="pytest",
            pytest_cmd="pytest",
        )
        result_file_path, run_result = run_tests(
            str(test_path),
            test_framework="pytest",
            cwd=str(project_root_path),
            pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
            pytest_cmd="pytest",
            verbose=True,
            test_env=test_env,
        )

        test_results = parse_test_results(
            test_xml_path=result_file_path,
            test_py_path=str(test_path),
            test_config=test_cfg,
            test_type=test_type,
            run_result=run_result,
            optimization_iteration=0,
        )

        assert test_results[0].id.function_getting_tested == "sorter"
        assert test_results[0].id.iteration_id == "4_0"
        assert test_results[0].id.test_class_name is None
        assert test_results[0].id.test_function_name == "test_sort_parametrized"
        assert (
            test_results[0].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_results_temp"
        )
        assert test_results[0].runtime > 0
        assert test_results[0].did_pass

        assert test_results[1].id.function_getting_tested == "sorter"
        assert test_results[1].id.iteration_id == "4_1"
        assert test_results[1].id.test_class_name is None
        assert test_results[1].id.test_function_name == "test_sort_parametrized"
        assert (
            test_results[1].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_results_temp"
        )
        assert test_results[1].runtime > 0
        assert test_results[1].did_pass

        assert test_results[2].id.function_getting_tested == "sorter"
        assert test_results[2].id.iteration_id == "4_2"
        assert test_results[2].id.test_class_name is None
        assert test_results[2].id.test_function_name == "test_sort_parametrized"
        assert (
            test_results[2].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_results_temp"
        )
        assert test_results[2].runtime > 0
        assert test_results[2].did_pass

    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)


def test_perfinjector_bubble_sort_parametrized_loop_results() -> None:
    code = """from code_to_optimize.bubble_sort import sorter
import pytest


@pytest.mark.parametrize(
    "input, expected_output",
    [
        ([5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5]),
        ([5.0, 4.0, 3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]),
        (list(reversed(range(50))), list(range(50))),
    ],
)
def test_sort_parametrized_loop(input, expected_output):
    for i in range(2):
        output = sorter(input)
        assert output == expected_output
"""
    expected = """import gc
import os
import sqlite3
import time

import dill as pickle
import pytest
import timeout_decorator

from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

@pytest.mark.parametrize('input, expected_output', [([5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5]), ([5.0, 4.0, 3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]), (list(reversed(range(50))), list(range(50)))])
def test_sort_parametrized_loop(input, expected_output):
    codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
    codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
    codeflash_cur = codeflash_con.cursor()
    codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
    for i in range(2):
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', None, 'test_sort_parametrized_loop', 'sorter', '4_0', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        assert output == expected_output
    codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/pytest/test_perfinjector_bubble_sort_parametrized_loop_results_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/pytest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "sorter", project_root_path, "pytest"
        )
        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.pytest.test_perfinjector_bubble_sort_parametrized_loop_results_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")

        # Overwrite old test with new instrumented test
        with open(test_path, "w") as f:
            f.write(new_test)

        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = "0"
        test_type = TestType.EXISTING_UNIT_TEST
        test_cfg = TestConfig(
            tests_root=str(tests_root),
            project_root_path=str(project_root_path),
            test_framework="pytest",
            pytest_cmd="pytest",
        )
        result_file_path, run_result = run_tests(
            str(test_path),
            test_framework="pytest",
            cwd=str(project_root_path),
            pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
            pytest_cmd="pytest",
            verbose=True,
            test_env=test_env,
        )

        test_results = parse_test_results(
            test_xml_path=result_file_path,
            test_py_path=str(test_path),
            test_config=test_cfg,
            test_type=test_type,
            run_result=run_result,
            optimization_iteration=0,
        )

        assert test_results[0].id.function_getting_tested == "sorter"
        assert test_results[0].id.iteration_id == "4_0_0"
        assert test_results[0].id.test_class_name is None
        assert test_results[0].id.test_function_name == "test_sort_parametrized_loop"
        assert (
            test_results[0].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_loop_results_temp"
        )
        assert test_results[0].runtime > 0
        assert test_results[0].did_pass

        assert test_results[1].id.function_getting_tested == "sorter"
        assert test_results[1].id.iteration_id == "4_0_1"
        assert test_results[1].id.test_class_name is None
        assert test_results[1].id.test_function_name == "test_sort_parametrized_loop"
        assert (
            test_results[1].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_loop_results_temp"
        )
        assert test_results[1].runtime > 0
        assert test_results[1].did_pass

        assert test_results[2].id.function_getting_tested == "sorter"
        assert test_results[2].id.iteration_id == "4_0_2"
        assert test_results[2].id.test_class_name is None
        assert test_results[2].id.test_function_name == "test_sort_parametrized_loop"
        assert (
            test_results[2].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_loop_results_temp"
        )
        assert test_results[2].runtime > 0
        assert test_results[2].did_pass

        assert test_results[3].id.function_getting_tested == "sorter"
        assert test_results[3].id.iteration_id == "4_0_3"
        assert test_results[3].id.test_class_name is None
        assert test_results[3].id.test_function_name == "test_sort_parametrized_loop"
        assert (
            test_results[3].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_loop_results_temp"
        )
        assert test_results[3].runtime > 0
        assert test_results[3].did_pass

        assert test_results[4].id.function_getting_tested == "sorter"
        assert test_results[4].id.iteration_id == "4_0_4"
        assert test_results[4].id.test_class_name is None
        assert test_results[4].id.test_function_name == "test_sort_parametrized_loop"
        assert (
            test_results[4].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_loop_results_temp"
        )
        assert test_results[4].runtime > 0
        assert test_results[4].did_pass

        assert test_results[5].id.function_getting_tested == "sorter"
        assert test_results[5].id.iteration_id == "4_0_5"
        assert test_results[5].id.test_class_name is None
        assert test_results[5].id.test_function_name == "test_sort_parametrized_loop"
        assert (
            test_results[5].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_parametrized_loop_results_temp"
        )
        assert test_results[5].runtime > 0
        assert test_results[5].did_pass
    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)


def test_perfinjector_bubble_sort_loop_results() -> None:
    code = """from code_to_optimize.bubble_sort import sorter


def test_sort():
    inputs = [[5, 4, 3, 2, 1, 0], [5.0, 4.0, 3.0, 2.0, 1.0, 0.0], list(reversed(range(50)))]
    expected_outputs = [[0, 1, 2, 3, 4, 5], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], list(range(50))]

    for i in range(3):
        input = inputs[i]
        expected_output = expected_outputs[i]
        output = sorter(input)
        assert output == expected_output"""

    expected = """import gc
import os
import sqlite3
import time

import dill as pickle
import timeout_decorator

from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

def test_sort():
    codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
    codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
    codeflash_cur = codeflash_con.cursor()
    codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
    inputs = [[5, 4, 3, 2, 1, 0], [5.0, 4.0, 3.0, 2.0, 1.0, 0.0], list(reversed(range(50)))]
    expected_outputs = [[0, 1, 2, 3, 4, 5], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], list(range(50))]
    for i in range(3):
        input = inputs[i]
        expected_output = expected_outputs[i]
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', None, 'test_sort', 'sorter', '6_2', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        assert output == expected_output
    codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/pytest/test_perfinjector_bubble_sort_loop_results_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/pytest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "sorter", project_root_path, "pytest"
        )
        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.pytest.test_perfinjector_bubble_sort_loop_results_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")

        # Overwrite old test with new instrumented test
        with open(test_path, "w") as f:
            f.write(new_test)

        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = "0"
        test_type = TestType.EXISTING_UNIT_TEST
        test_cfg = TestConfig(
            tests_root=str(tests_root),
            project_root_path=str(project_root_path),
            test_framework="pytest",
            pytest_cmd="pytest",
        )
        result_file_path, run_result = run_tests(
            str(test_path),
            test_framework="pytest",
            cwd=str(project_root_path),
            pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
            pytest_cmd="pytest",
            verbose=True,
            test_env=test_env,
        )
        test_results = parse_test_results(
            test_xml_path=result_file_path,
            test_py_path=str(test_path),
            test_config=test_cfg,
            test_type=test_type,
            run_result=run_result,
            optimization_iteration=0,
        )

        assert test_results[0].id.function_getting_tested == "sorter"
        assert test_results[0].id.iteration_id == "6_2_0"
        assert test_results[0].id.test_class_name is None
        assert test_results[0].id.test_function_name == "test_sort"
        assert (
            test_results[0].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_loop_results_temp"
        )
        assert test_results[0].runtime > 0
        assert test_results[0].did_pass

        assert test_results[1].id.function_getting_tested == "sorter"
        assert test_results[1].id.iteration_id == "6_2_1"
        assert test_results[1].id.test_class_name is None
        assert test_results[1].id.test_function_name == "test_sort"
        assert (
            test_results[1].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_loop_results_temp"
        )
        assert test_results[1].runtime > 0
        assert test_results[1].did_pass

        assert test_results[2].id.function_getting_tested == "sorter"
        assert test_results[2].id.iteration_id == "6_2_2"
        assert test_results[2].id.test_class_name is None
        assert test_results[2].id.test_function_name == "test_sort"
        assert (
            test_results[2].id.test_module_path
            == "tests.pytest.test_perfinjector_bubble_sort_loop_results_temp"
        )
        assert test_results[2].runtime > 0
        assert test_results[2].did_pass
    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)


def test_perfinjector_bubble_sort_unittest_results() -> None:
    code = """import unittest

from code_to_optimize.bubble_sort import sorter


class TestPigLatin(unittest.TestCase):
    def test_sort(self):
        input = [5, 4, 3, 2, 1, 0]
        output = sorter(input)
        self.assertEqual(output, [0, 1, 2, 3, 4, 5])

        input = [5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
        output = sorter(input)
        self.assertEqual(output, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])

        input = list(reversed(range(50)))
        output = sorter(input)
        self.assertEqual(output, list(range(50)))
"""

    expected = """import gc
import os
import sqlite3
import time
import unittest

import dill as pickle
import timeout_decorator
from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

class TestPigLatin(unittest.TestCase):

    @timeout_decorator.timeout(15)
    def test_sort(self):
        codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
        codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
        codeflash_cur = codeflash_con.cursor()
        codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
        input = [5, 4, 3, 2, 1, 0]
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '5', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        self.assertEqual(output, [0, 1, 2, 3, 4, 5])
        input = [5.0, 4.0, 3.0, 2.0, 1.0, 0.0]
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '8', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        self.assertEqual(output, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        input = list(reversed(range(50)))
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '11', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        self.assertEqual(output, list(range(50)))
        codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/unittest/test_perfinjector_bubble_sort_unittest_results_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/unittest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "sorter", project_root_path, "unittest"
        )

        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.unittest.test_perfinjector_bubble_sort_unittest_results_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")

        # Overwrite old test with new instrumented test
        with open(test_path, "w") as f:
            f.write(new_test)

        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = "0"
        test_type = TestType.EXISTING_UNIT_TEST

        test_cfg = TestConfig(
            tests_root=str(tests_root),
            project_root_path=str(project_root_path),
            test_framework="unittest",
        )

        result_file_path, run_result = run_tests(
            str(test_path),
            test_framework="unittest",
            cwd=str(project_root_path),
            pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
            pytest_cmd="pytest",
            verbose=True,
            test_env=test_env,
        )
        test_results = parse_test_results(
            test_xml_path=result_file_path,
            test_py_path=str(test_path),
            test_config=test_cfg,
            test_type=test_type,
            run_result=run_result,
            optimization_iteration=0,
        )

        assert test_results[0].id.function_getting_tested == "sorter"
        assert test_results[0].id.iteration_id == "5_0"
        assert test_results[0].id.test_class_name == "TestPigLatin"
        assert test_results[0].id.test_function_name == "test_sort"
        assert (
            test_results[0].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_results_temp"
        )
        assert test_results[0].runtime > 0
        assert test_results[0].did_pass

        assert test_results[1].id.function_getting_tested == "sorter"
        assert test_results[1].id.iteration_id == "8_0"
        assert test_results[1].id.test_class_name == "TestPigLatin"
        assert test_results[1].id.test_function_name == "test_sort"
        assert (
            test_results[1].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_results_temp"
        )
        assert test_results[1].runtime > 0
        assert test_results[1].did_pass

        assert test_results[2].id.function_getting_tested == "sorter"
        assert test_results[2].id.iteration_id == "11_0"
        assert test_results[2].id.test_class_name == "TestPigLatin"
        assert test_results[2].id.test_function_name == "test_sort"
        assert (
            test_results[2].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_results_temp"
        )
        assert test_results[2].runtime > 0
        assert test_results[2].did_pass
    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)


def test_perfinjector_bubble_sort_unittest_parametrized_results() -> None:
    code = """import unittest
from parameterized import parameterized

from code_to_optimize.bubble_sort import sorter


class TestPigLatin(unittest.TestCase):
    @parameterized.expand(
        [
            ([5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5]),
            ([5.0, 4.0, 3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]),
            (list(reversed(range(50))), list(range(50))),
        ]
    )
    def test_sort(self, input, expected_output):
        output = sorter(input)
        self.assertEqual(output, expected_output)
"""

    expected = """import gc
import os
import sqlite3
import time
import unittest

import dill as pickle
import timeout_decorator
from parameterized import parameterized

from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

class TestPigLatin(unittest.TestCase):

    @parameterized.expand([([5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5]), ([5.0, 4.0, 3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]), (list(reversed(range(50))), list(range(50)))])
    @timeout_decorator.timeout(15)
    def test_sort(self, input, expected_output):
        codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
        codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
        codeflash_cur = codeflash_con.cursor()
        codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
        codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '4', codeflash_cur, codeflash_con, input)
        output = codeflash_return_value
        self.assertEqual(output, expected_output)
        codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/unittest/test_perfinjector_bubble_sort_unittest_parametrized_results_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/unittest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "sorter", project_root_path, "unittest"
        )
        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_results_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")

        # Overwrite old test with new instrumented test
        with open(test_path, "w") as f:
            f.write(new_test)

        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = "0"
        test_type = TestType.EXISTING_UNIT_TEST
        test_cfg = TestConfig(
            tests_root=str(tests_root),
            project_root_path=str(project_root_path),
            test_framework="unittest",
        )
        result_file_path, run_result = run_tests(
            str(test_path),
            test_framework="unittest",
            cwd=str(project_root_path),
            pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
            pytest_cmd="pytest",
            verbose=True,
            test_env=test_env,
        )

        test_results = parse_test_results(
            test_xml_path=result_file_path,
            test_py_path=str(test_path),
            test_config=test_cfg,
            test_type=test_type,
            run_result=run_result,
            optimization_iteration=0,
        )

        assert test_results[0].id.function_getting_tested == "sorter"
        assert test_results[0].id.iteration_id == "4_0"
        assert test_results[0].id.test_class_name == "TestPigLatin"
        assert test_results[0].id.test_function_name == "test_sort"
        assert (
            test_results[0].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_results_temp"
        )
        assert test_results[0].runtime > 0
        assert test_results[0].did_pass

        assert test_results[1].id.function_getting_tested == "sorter"
        assert test_results[1].id.iteration_id == "4_1"
        assert test_results[1].id.test_class_name == "TestPigLatin"
        assert test_results[1].id.test_function_name == "test_sort"
        assert (
            test_results[1].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_results_temp"
        )
        assert test_results[1].runtime > 0
        assert test_results[1].did_pass

        assert test_results[2].id.function_getting_tested == "sorter"
        assert test_results[2].id.iteration_id == "4_2"
        assert test_results[2].id.test_class_name == "TestPigLatin"
        assert test_results[2].id.test_function_name == "test_sort"
        assert (
            test_results[2].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_results_temp"
        )
        assert test_results[2].runtime > 0
        assert test_results[2].did_pass

    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)


def test_perfinjector_bubble_sort_unittest_loop_results() -> None:
    code = """import unittest

from code_to_optimize.bubble_sort import sorter


class TestPigLatin(unittest.TestCase):
    def test_sort(self):
        inputs = [[5, 4, 3, 2, 1, 0], [5.0, 4.0, 3.0, 2.0, 1.0, 0.0], list(reversed(range(50)))]
        expected_outputs = [[0, 1, 2, 3, 4, 5], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], list(range(50))]

        for i in range(3):
            input = inputs[i]
            expected_output = expected_outputs[i]
            output = sorter(input)
            self.assertEqual(output, expected_output)"""

    expected = """import gc
import os
import sqlite3
import time
import unittest

import dill as pickle
import timeout_decorator

from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

class TestPigLatin(unittest.TestCase):

    @timeout_decorator.timeout(15)
    def test_sort(self):
        codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
        codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
        codeflash_cur = codeflash_con.cursor()
        codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
        inputs = [[5, 4, 3, 2, 1, 0], [5.0, 4.0, 3.0, 2.0, 1.0, 0.0], list(reversed(range(50)))]
        expected_outputs = [[0, 1, 2, 3, 4, 5], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], list(range(50))]
        for i in range(3):
            input = inputs[i]
            expected_output = expected_outputs[i]
            codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '6_2', codeflash_cur, codeflash_con, input)
            output = codeflash_return_value
            self.assertEqual(output, expected_output)
        codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/unittest/test_perfinjector_bubble_sort_unittest_loop_results_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/unittest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "sorter", project_root_path, "unittest"
        )
        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.unittest.test_perfinjector_bubble_sort_unittest_loop_results_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")

        # Overwrite old test with new instrumented test
        with open(test_path, "w") as f:
            f.write(new_test)

        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = "0"
        test_type = TestType.EXISTING_UNIT_TEST

        test_cfg = TestConfig(
            tests_root=str(tests_root),
            project_root_path=str(project_root_path),
            test_framework="unittest",
        )

        result_file_path, run_result = run_tests(
            str(test_path),
            test_framework="unittest",
            cwd=str(project_root_path),
            pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
            pytest_cmd="pytest",
            verbose=True,
            test_env=test_env,
        )
        test_results = parse_test_results(
            test_xml_path=result_file_path,
            test_py_path=str(test_path),
            test_config=test_cfg,
            test_type=test_type,
            run_result=run_result,
            optimization_iteration=0,
        )

        assert test_results[0].id.function_getting_tested == "sorter"
        assert test_results[0].id.iteration_id == "6_2_0"
        assert test_results[0].id.test_class_name == "TestPigLatin"
        assert test_results[0].id.test_function_name == "test_sort"
        assert (
            test_results[0].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_loop_results_temp"
        )
        assert test_results[0].runtime > 0
        assert test_results[0].did_pass

        assert test_results[1].id.function_getting_tested == "sorter"
        assert test_results[1].id.iteration_id == "6_2_1"
        assert test_results[1].id.test_class_name == "TestPigLatin"
        assert test_results[1].id.test_function_name == "test_sort"
        assert (
            test_results[1].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_loop_results_temp"
        )
        assert test_results[1].runtime > 0
        assert test_results[1].did_pass

        assert test_results[2].id.function_getting_tested == "sorter"
        assert test_results[2].id.iteration_id == "6_2_2"
        assert test_results[2].id.test_class_name == "TestPigLatin"
        assert test_results[2].id.test_function_name == "test_sort"
        assert (
            test_results[2].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_loop_results_temp"
        )
        assert test_results[2].runtime > 0
        assert test_results[2].did_pass
    finally:
        os.remove(test_path)


def test_perfinjector_bubble_sort_unittest_parametrized_loop_results() -> None:
    code = """import unittest
from parameterized import parameterized

from code_to_optimize.bubble_sort import sorter


class TestPigLatin(unittest.TestCase):
    @parameterized.expand(
        [
            ([5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5]),
            ([5.0, 4.0, 3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]),
            (list(reversed(range(50))), list(range(50))),
        ]
    )
    def test_sort(self, input, expected_output):
        for i in range(2):
            output = sorter(input)
            self.assertEqual(output, expected_output)
"""

    expected = """import gc
import os
import sqlite3
import time
import unittest

import dill as pickle
import timeout_decorator
from parameterized import parameterized

from code_to_optimize.bubble_sort import sorter


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

class TestPigLatin(unittest.TestCase):

    @parameterized.expand([([5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5]), ([5.0, 4.0, 3.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]), (list(reversed(range(50))), list(range(50)))])
    @timeout_decorator.timeout(15)
    def test_sort(self, input, expected_output):
        codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
        codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
        codeflash_cur = codeflash_con.cursor()
        codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
        for i in range(2):
            codeflash_return_value = codeflash_wrap(sorter, '{module_path}', 'TestPigLatin', 'test_sort', 'sorter', '4_0', codeflash_cur, codeflash_con, input)
            output = codeflash_return_value
            self.assertEqual(output, expected_output)
        codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/unittest/test_perfinjector_bubble_sort_unittest_parametrized_loop_results_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/unittest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "sorter", project_root_path, "unittest"
        )
        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_loop_results_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")

        # Overwrite old test with new instrumented test
        with open(test_path, "w") as f:
            f.write(new_test)

        test_env = os.environ.copy()
        test_env["CODEFLASH_TEST_ITERATION"] = "0"
        test_type = TestType.EXISTING_UNIT_TEST

        test_cfg = TestConfig(
            tests_root=str(tests_root),
            project_root_path=str(project_root_path),
            test_framework="unittest",
            pytest_cmd="pytest",
        )
        result_file_path, run_result = run_tests(
            str(test_path),
            test_framework="unittest",
            cwd=str(project_root_path),
            pytest_timeout=INDIVIDUAL_TESTCASE_TIMEOUT,
            pytest_cmd="pytest",
            verbose=True,
            test_env=test_env,
        )

        test_results = parse_test_results(
            test_xml_path=result_file_path,
            test_py_path=str(test_path),
            test_config=test_cfg,
            test_type=test_type,
            run_result=run_result,
            optimization_iteration=0,
        )

        assert test_results[0].id.function_getting_tested == "sorter"
        assert test_results[0].id.iteration_id == "4_0_0"
        assert test_results[0].id.test_class_name == "TestPigLatin"
        assert test_results[0].id.test_function_name == "test_sort"
        assert (
            test_results[0].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_loop_results_temp"
        )
        assert test_results[0].runtime > 0
        assert test_results[0].did_pass

        assert test_results[1].id.function_getting_tested == "sorter"
        assert test_results[1].id.iteration_id == "4_0_1"
        assert test_results[1].id.test_class_name == "TestPigLatin"
        assert test_results[1].id.test_function_name == "test_sort"
        assert (
            test_results[1].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_loop_results_temp"
        )
        assert test_results[1].runtime > 0
        assert test_results[1].did_pass

        assert test_results[2].id.function_getting_tested == "sorter"
        assert test_results[2].id.iteration_id == "4_0_2"
        assert test_results[2].id.test_class_name == "TestPigLatin"
        assert test_results[2].id.test_function_name == "test_sort"
        assert (
            test_results[2].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_loop_results_temp"
        )
        assert test_results[2].runtime > 0
        assert test_results[2].did_pass

        assert test_results[3].id.function_getting_tested == "sorter"
        assert test_results[3].id.iteration_id == "4_0_3"
        assert test_results[3].id.test_class_name == "TestPigLatin"
        assert test_results[3].id.test_function_name == "test_sort"
        assert (
            test_results[3].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_loop_results_temp"
        )
        assert test_results[3].runtime > 0
        assert test_results[3].did_pass

        assert test_results[4].id.function_getting_tested == "sorter"
        assert test_results[4].id.iteration_id == "4_0_4"
        assert test_results[4].id.test_class_name == "TestPigLatin"
        assert test_results[4].id.test_function_name == "test_sort"
        assert (
            test_results[4].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_loop_results_temp"
        )
        assert test_results[4].runtime > 0
        assert test_results[4].did_pass

        assert test_results[5].id.function_getting_tested == "sorter"
        assert test_results[5].id.iteration_id == "4_0_5"
        assert test_results[5].id.test_class_name == "TestPigLatin"
        assert test_results[5].id.test_function_name == "test_sort"
        assert (
            test_results[5].id.test_module_path
            == "tests.unittest.test_perfinjector_bubble_sort_unittest_parametrized_loop_results_temp"
        )
        assert test_results[5].runtime > 0
        assert test_results[5].did_pass
    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)


def test_update_line_node() -> None:
    injectperf = InjectPerfOnly(
        "sorter",
        "code_to_optimize.tests.pytest.test_bubble_sort",
    )
    node = ast.Assign(
        targets=[ast.Name(id="output", ctx=ast.Store())],
        value=ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="sort", ctx=ast.Load()),
                attr="sorter",
                ctx=ast.Load(),
                lineno=2,
                col_offset=1,
            ),
            args=[ast.Name(id="input", ctx=ast.Load())],
            keywords=[],
        ),
        lineno=1,
        col_offset=1,
    )

    assert len(injectperf.update_line_node(node, "test_sort", "0", None)) > 0


def test_class_method_imported_as() -> None:
    code = """import functionA
import moduleB as module_B
from module import functionB as function_B
import class_name_B
from nuitka.nodes.ImportNodes import ExpressionBuiltinImport as nuitka_nodes_ImportNodes_ExpressionBuiltinImport
"""
    tree = ast.parse(code)
    visitor = FunctionImportedAsVisitor("functionA")
    visitor.visit(tree)
    assert visitor.imported_as == "functionA"

    visitor = FunctionImportedAsVisitor("functionB")
    visitor.visit(tree)
    assert visitor.imported_as == "function_B"

    visitor = FunctionImportedAsVisitor("ExpressionBuiltinImport.method_name")
    visitor.visit(tree)
    assert (
        visitor.imported_as
        == "nuitka_nodes_ImportNodes_ExpressionBuiltinImport.method_name"
    )

    visitor = FunctionImportedAsVisitor("class_name_B")
    visitor.visit(tree)
    assert visitor.imported_as == "class_name_B"


def test_class_function_instrumentation() -> None:
    code = """from module import class_name as class_name_A

def test_class_name_A_function_name():
    ret = class_name_A.function_name(**args)
"""

    expected = """import gc
import os
import sqlite3
import time

import dill as pickle
import timeout_decorator
from module import class_name as class_name_A


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

def test_class_name_A_function_name():
    codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
    codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
    codeflash_cur = codeflash_con.cursor()
    codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
    codeflash_return_value = codeflash_wrap(class_name_A.function_name, '{module_path}', None, 'test_class_name_A_function_name', 'class_name_A.function_name', '4', codeflash_cur, codeflash_con, **args)
    ret = codeflash_return_value
    codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/pytest/test_class_function_instrumentation_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "class_name.function_name", project_root_path, "pytest"
        )
    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)
    assert success
    assert new_test.replace('"', "'") == expected.format(
        tmp_dir_path=get_run_tmp_file("test_return_values"),
        module_path="tests.pytest.test_class_function_instrumentation_temp",
    ).replace('"', "'")


def test_wrong_function_instrumentation() -> None:
    code = """from codeflash.result.common_tags import find_common_tags


def test_common_tags_1():
    articles_1 = [1, 2, 3]

    assert find_common_tags(articles_1) == set(1, 2)

    articles_2 = [1, 2]

    assert find_common_tags(articles_2) == set(1)
"""

    expected = """import gc
import os
import sqlite3
import time

import dill as pickle
import timeout_decorator

from codeflash.result.common_tags import find_common_tags


def codeflash_wrap(wrapped, test_module_name, test_class_name, test_name, function_name, line_id, codeflash_cur, codeflash_con, *args, **kwargs):
    test_id = f'{{test_module_name}}:{{test_class_name}}:{{test_name}}:{{line_id}}'
    if not hasattr(codeflash_wrap, 'index'):
        codeflash_wrap.index = {{}}
    if test_id in codeflash_wrap.index:
        codeflash_wrap.index[test_id] += 1
    else:
        codeflash_wrap.index[test_id] = 0
    codeflash_test_index = codeflash_wrap.index[test_id]
    invocation_id = f'{{line_id}}_{{codeflash_test_index}}'
    print(f"!######{{test_module_name}}:{{(test_class_name + '.' if test_class_name else '')}}{{test_name}}:{{function_name}}:{{invocation_id}}######!")
    gc.disable()
    counter = time.perf_counter_ns()
    return_value = wrapped(*args, **kwargs)
    codeflash_duration = time.perf_counter_ns() - counter
    gc.enable()
    codeflash_cur.execute('INSERT INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?)', (test_module_name, test_class_name, test_name, function_name, invocation_id, codeflash_duration, pickle.dumps(return_value)))
    codeflash_con.commit()
    return return_value

def test_common_tags_1():
    codeflash_iteration = os.environ['CODEFLASH_TEST_ITERATION']
    codeflash_con = sqlite3.connect(f'{tmp_dir_path}_{{codeflash_iteration}}.sqlite')
    codeflash_cur = codeflash_con.cursor()
    codeflash_cur.execute('CREATE TABLE IF NOT EXISTS test_results (test_module_path TEXT, test_class_name TEXT, test_function_name TEXT, function_getting_tested TEXT, iteration_id TEXT, runtime INTEGER, return_value BLOB)')
    articles_1 = [1, 2, 3]
    codeflash_return_value = codeflash_wrap(find_common_tags, '{module_path}', None, 'test_common_tags_1', 'find_common_tags', '5', codeflash_cur, codeflash_con, articles_1)
    assert codeflash_return_value == set(1, 2)
    articles_2 = [1, 2]
    codeflash_return_value = codeflash_wrap(find_common_tags, '{module_path}', None, 'test_common_tags_1', 'find_common_tags', '7', codeflash_cur, codeflash_con, articles_2)
    assert codeflash_return_value == set(1)
    codeflash_con.close()
"""

    test_path = (
        pathlib.Path(__file__).parent.resolve()
        / "../code_to_optimize/tests/pytest/test_wrong_function_instrumentation_temp.py"
    )
    try:
        with open(test_path, "w") as f:
            f.write(code)

        tests_root = (
            pathlib.Path(__file__).parent.resolve()
            / "../code_to_optimize/tests/pytest/"
        )
        project_root_path = (
            pathlib.Path(__file__).parent.resolve() / "../code_to_optimize/"
        )

        success, new_test = inject_profiling_into_existing_test(
            test_path, "find_common_tags", project_root_path, "pytest"
        )
        assert success
        assert new_test.replace('"', "'") == expected.format(
            module_path="tests.pytest.test_wrong_function_instrumentation_temp",
            tmp_dir_path=get_run_tmp_file("test_return_values"),
        ).replace('"', "'")
    finally:
        pathlib.Path(test_path).unlink(missing_ok=True)
