import os
import pathlib
import tempfile

from codeflash.discovery.discover_unit_tests import discover_unit_tests
from codeflash.verification.verification_utils import TestConfig


def test_unit_test_discovery_pytest():
    project_path = pathlib.Path(__file__).parent.parent.resolve() / "code_to_optimize"
    tests_path = project_path / "tests" / "pytest"
    test_config = TestConfig(
        tests_root=str(tests_path), project_root_path=str(project_path), test_framework="pytest",
    )
    tests = discover_unit_tests(test_config)
    assert len(tests) > 0
    # print(tests)


def test_unit_test_discovery_unittest():
    project_path = pathlib.Path(__file__).parent.parent.resolve() / "code_to_optimize"
    test_path = project_path / "tests" / "unittest"
    test_config = TestConfig(
        tests_root=str(project_path), project_root_path=str(project_path), test_framework="unittest",
    )
    os.chdir(str(project_path))
    tests = discover_unit_tests(test_config)
    # assert len(tests) > 0
    # Unittest discovery within a pytest environment does not work


def test_discover_tests_pytest_with_temp_dir_root():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create a dummy test file
        test_file_path = pathlib.Path(tmpdirname) / "test_dummy.py"
        test_file_content = (
            "from dummy_code import dummy_function\n\n"
            "def test_dummy_function():\n"
            "    assert dummy_function() is True\n"
        )
        test_file_path.write_text(test_file_content)

        # Create a file that the test file is testing
        code_file_path = pathlib.Path(tmpdirname) / "dummy_code.py"
        code_file_content = "def dummy_function():\n    return True\n"
        code_file_path.write_text(code_file_content)

        # Create a TestConfig with the temporary directory as the root
        test_config = TestConfig(
            tests_root=str(tmpdirname), project_root_path=str(tmpdirname), test_framework="pytest",
        )

        # Discover tests
        discovered_tests = discover_unit_tests(test_config)

        # Check if the dummy test file is discovered
        assert len(discovered_tests) == 1
        assert discovered_tests["dummy_code.dummy_function"][0].test_file == str(test_file_path)


def test_discover_tests_pytest_with_multi_level_dirs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create multi-level directories
        level1_dir = pathlib.Path(tmpdirname) / "level1"
        level2_dir = level1_dir / "level2"
        level2_dir.mkdir(parents=True)

        # Create code files at each level
        root_code_file_path = pathlib.Path(tmpdirname) / "root_code.py"
        root_code_file_content = "def root_function():\n    return True\n"
        root_code_file_path.write_text(root_code_file_content)

        level1_code_file_path = level1_dir / "level1_code.py"
        level1_code_file_content = "def level1_function():\n    return True\n"
        level1_code_file_path.write_text(level1_code_file_content)

        level2_code_file_path = level2_dir / "level2_code.py"
        level2_code_file_content = "def level2_function():\n    return True\n"
        level2_code_file_path.write_text(level2_code_file_content)

        # Create a test file at the root level
        root_test_file_path = pathlib.Path(tmpdirname) / "test_root.py"
        root_test_file_content = (
            "from root_code import root_function\n\n"
            "def test_root_function():\n"
            "    assert True\n"
            "    assert root_function() is True\n"
        )
        root_test_file_path.write_text(root_test_file_content)

        # Create a test file at level 1
        level1_test_file_path = level1_dir / "test_level1.py"
        level1_test_file_content = (
            "from level1_code import level1_function\n\n"
            "def test_level1_function():\n"
            "    assert True\n"
            "    assert level1_function() is True\n"
        )
        level1_test_file_path.write_text(level1_test_file_content)

        # Create a test file at level 2
        level2_test_file_path = level2_dir / "test_level2.py"
        level2_test_file_content = (
            "from level2_code import level2_function\n\n"
            "def test_level2_function():\n"
            "    assert True\n"
            "    assert level2_function() is True\n"
        )
        level2_test_file_path.write_text(level2_test_file_content)

        # Create a TestConfig with the temporary directory as the root
        test_config = TestConfig(
            tests_root=str(tmpdirname), project_root_path=str(tmpdirname), test_framework="pytest",
        )

        # Discover tests
        discovered_tests = discover_unit_tests(test_config)

        # Check if the test files at all levels are discovered
        assert len(discovered_tests) == 3
        assert discovered_tests["root_code.root_function"][0].test_file == str(root_test_file_path)
        assert discovered_tests["level1_code.level1_function"][0].test_file == str(
            level1_test_file_path,
        )
        assert discovered_tests["level2_code.level2_function"][0].test_file == str(
            level2_test_file_path,
        )


def test_discover_tests_pytest_dirs():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create multi-level directories
        level1_dir = pathlib.Path(tmpdirname) / "level1"
        level2_dir = level1_dir / "level2"
        level2_dir.mkdir(parents=True)
        level3_dir = level1_dir / "level3"
        level3_dir.mkdir(parents=True)

        # Create code files at each level
        root_code_file_path = pathlib.Path(tmpdirname) / "root_code.py"
        root_code_file_content = "def root_function():\n    return True\n"
        root_code_file_path.write_text(root_code_file_content)

        level1_code_file_path = level1_dir / "level1_code.py"
        level1_code_file_content = "def level1_function():\n    return True\n"
        level1_code_file_path.write_text(level1_code_file_content)

        level2_code_file_path = level2_dir / "level2_code.py"
        level2_code_file_content = "def level2_function():\n    return True\n"
        level2_code_file_path.write_text(level2_code_file_content)

        level3_code_file_path = level3_dir / "level3_code.py"
        level3_code_file_content = "def level3_function():\n    return True\n"
        level3_code_file_path.write_text(level3_code_file_content)

        # Create a test file at the root level
        root_test_file_path = pathlib.Path(tmpdirname) / "test_root.py"
        root_test_file_content = (
            "from root_code import root_function\n\n"
            "def test_root_function():\n"
            "    assert True\n"
            "    assert root_function() is True\n"
        )
        root_test_file_path.write_text(root_test_file_content)

        # Create a test file at level 1
        level1_test_file_path = level1_dir / "test_level1.py"
        level1_test_file_content = (
            "from level1_code import level1_function\n\n"
            "def test_level1_function():\n"
            "    assert True\n"
            "    assert level1_function() is True\n"
        )
        level1_test_file_path.write_text(level1_test_file_content)

        # Create a test file at level 2
        level2_test_file_path = level2_dir / "test_level2.py"
        level2_test_file_content = (
            "from level2_code import level2_function\n\n"
            "def test_level2_function():\n"
            "    assert True\n"
            "    assert level2_function() is True\n"
        )
        level2_test_file_path.write_text(level2_test_file_content)

        level3_test_file_path = level3_dir / "test_level3.py"
        level3_test_file_content = (
            "from level3_code import level3_function\n\n"
            "def test_level3_function():\n"
            "    assert True\n"
            "    assert level3_function() is True\n"
        )
        level3_test_file_path.write_text(level3_test_file_content)

        # Create a TestConfig with the temporary directory as the root
        test_config = TestConfig(
            tests_root=str(tmpdirname), project_root_path=str(tmpdirname), test_framework="pytest",
        )

        # Discover tests
        discovered_tests = discover_unit_tests(test_config)

        # Check if the test files at all levels are discovered
        assert len(discovered_tests) == 4
        assert discovered_tests["root_code.root_function"][0].test_file == str(root_test_file_path)
        assert discovered_tests["level1_code.level1_function"][0].test_file == str(
            level1_test_file_path,
        )
        assert discovered_tests["level2_code.level2_function"][0].test_file == str(
            level2_test_file_path,
        )
        assert discovered_tests["level3_code.level3_function"][0].test_file == str(
            level3_test_file_path,
        )


def test_discover_tests_pytest_with_class():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create a code file with a class
        code_file_path = pathlib.Path(tmpdirname) / "some_class_code.py"
        code_file_content = (
            "class SomeClass:\n    def some_method(self):\n        return True\n"
        )
        code_file_path.write_text(code_file_content)

        # Create a test file with a test class and a test method
        test_file_path = pathlib.Path(tmpdirname) / "test_some_class.py"
        test_file_content = (
            "from some_class_code import SomeClass\n\n"
            "def test_some_method():\n"
            "    instance = SomeClass()\n"
            "    assert instance.some_method() is True\n"
        )
        test_file_path.write_text(test_file_content)

        # Create a TestConfig with the temporary directory as the root
        test_config = TestConfig(
            tests_root=str(tmpdirname), project_root_path=str(tmpdirname), test_framework="pytest",
        )

        # Discover tests
        discovered_tests = discover_unit_tests(test_config)

        # Check if the test class and method are discovered
        assert len(discovered_tests) == 1
        assert discovered_tests["some_class_code.SomeClass.some_method"][0].test_file == str(
            test_file_path,
        )


def test_discover_tests_with_code_in_dir_and_test_in_subdir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create a directory for the code file
        code_dir = pathlib.Path(tmpdirname) / "code"
        code_dir.mkdir()

        # Create a code file in the code directory
        code_file_path = code_dir / "some_code.py"
        code_file_content = "def some_function():\n    return True\n"
        code_file_path.write_text(code_file_content)

        # Create a subdirectory for the test file within the code directory
        test_subdir = code_dir / "tests"
        test_subdir.mkdir()

        # Create a test file in the test subdirectory
        test_file_path = test_subdir / "test_some_code.py"
        test_file_content = (
            "import sys\n"
            "import os\n"
            "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))\n"
            "from some_code import some_function\n\n"
            "def test_some_function():\n"
            "    assert some_function() is True\n"
        )
        test_file_path.write_text(test_file_content)

        # Create a TestConfig with the code directory as the root
        test_config = TestConfig(
            tests_root=str(test_subdir), project_root_path=str(tmpdirname), test_framework="pytest",
        )

        # Discover tests
        discovered_tests = discover_unit_tests(test_config)

        # Check if the test file is discovered and associated with the code file
        assert len(discovered_tests) == 1
        assert discovered_tests["some_code.some_function"][0].test_file == str(test_file_path)
