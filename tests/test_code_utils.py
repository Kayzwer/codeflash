import ast
import site
from pathlib import Path

import pytest

from codeflash.code_utils.code_utils import (
    file_path_from_module_name,
    get_all_function_names,
    get_imports_from_file,
    get_run_tmp_file,
    is_class_defined_in_file,
    module_name_from_file_path,
    path_belongs_to_site_packages,
)


# tests for module_name_from_file_path
def test_module_name_from_file_path() -> None:
    project_root_path = Path("/Users/codeflashuser/PycharmProjects/codeflash")
    file_path = project_root_path / "cli/codeflash/code_utils/code_utils.py"

    module_name = module_name_from_file_path(file_path, project_root_path)
    assert module_name == "cli.codeflash.code_utils.code_utils"


def test_module_name_from_file_path_with_subdirectory() -> None:
    project_root_path = Path("/Users/codeflashuser/PycharmProjects/codeflash")
    file_path = project_root_path / "cli/codeflash/code_utils/subdir/code_utils.py"

    module_name = module_name_from_file_path(file_path, project_root_path)
    assert module_name == "cli.codeflash.code_utils.subdir.code_utils"


def test_module_name_from_file_path_with_different_root() -> None:
    project_root_path = Path("/Users/codeflashuser/PycharmProjects")
    file_path = project_root_path / "codeflash/cli/codeflash/code_utils/code_utils.py"

    module_name = module_name_from_file_path(file_path, project_root_path)
    assert module_name == "codeflash.cli.codeflash.code_utils.code_utils"


def test_module_name_from_file_path_with_root_as_file() -> None:
    project_root_path = Path("/Users/codeflashuser/PycharmProjects/codeflash/cli/codeflash/code_utils")
    file_path = project_root_path / "code_utils.py"

    module_name = module_name_from_file_path(file_path, project_root_path)
    assert module_name == "code_utils"


# tests for get_imports_from_file
def test_get_imports_from_file_with_file_path(tmp_path: Path) -> None:
    test_file = tmp_path / "test_file.py"
    test_file.write_text("import os\nfrom sys import path\n")

    imports = get_imports_from_file(file_path=test_file)
    assert len(imports) == 2
    assert isinstance(imports[0], ast.Import)
    assert isinstance(imports[1], ast.ImportFrom)
    assert imports[0].names[0].name == "os"
    assert imports[1].module == "sys"
    assert imports[1].names[0].name == "path"


def test_get_imports_from_file_with_file_string() -> None:
    file_string = "import os\nfrom sys import path\n"

    imports = get_imports_from_file(file_string=file_string)
    assert len(imports) == 2
    assert isinstance(imports[0], ast.Import)
    assert isinstance(imports[1], ast.ImportFrom)
    assert imports[0].names[0].name == "os"
    assert imports[1].module == "sys"
    assert imports[1].names[0].name == "path"


def test_get_imports_from_file_with_file_ast() -> None:
    file_string = "import os\nfrom sys import path\n"
    file_ast = ast.parse(file_string)

    imports = get_imports_from_file(file_ast=file_ast)
    assert len(imports) == 2
    assert isinstance(imports[0], ast.Import)
    assert isinstance(imports[1], ast.ImportFrom)
    assert imports[0].names[0].name == "os"
    assert imports[1].module == "sys"
    assert imports[1].names[0].name == "path"


def test_get_imports_from_file_with_syntax_error(caplog) -> None:
    file_string = "import os\nfrom sys import path\ninvalid syntax"

    imports = get_imports_from_file(file_string=file_string)
    assert len(imports) == 0
    assert "Syntax error in code" in caplog.text


def test_get_imports_from_file_with_no_input() -> None:
    with pytest.raises(
        AssertionError, match="Must provide exactly one of file_path, file_string, or file_ast"
    ):
        get_imports_from_file()


# tests for file_path_from_module_name
def test_file_path_from_module_name() -> None:
    project_root_path = Path("/Users/codeflashuser/PycharmProjects/codeflash")
    module_name = "cli.codeflash.code_utils.code_utils"

    file_path = file_path_from_module_name(module_name, project_root_path)
    assert file_path == project_root_path / "cli/codeflash/code_utils/code_utils.py"


def test_file_path_from_module_name_with_subdirectory() -> None:
    project_root_path = Path("/Users/codeflashuser/PycharmProjects/codeflash")
    module_name = "cli.codeflash.code_utils.subdir.code_utils"

    file_path = file_path_from_module_name(module_name, project_root_path)
    assert file_path == project_root_path / "cli/codeflash/code_utils/subdir/code_utils.py"


def test_file_path_from_module_name_with_different_root() -> None:
    project_root_path = Path("/Users/codeflashuser/PycharmProjects")
    module_name = "codeflash.cli.codeflash.code_utils.code_utils"

    file_path = file_path_from_module_name(module_name, project_root_path)
    assert file_path == project_root_path / "codeflash/cli/codeflash/code_utils/code_utils.py"


def test_file_path_from_module_name_with_root_as_file() -> None:
    project_root_path = Path("/Users/codeflashuser/PycharmProjects/codeflash/cli/codeflash/code_utils")
    module_name = "code_utils"

    file_path = file_path_from_module_name(module_name, project_root_path)
    assert file_path == project_root_path / "code_utils.py"


# tests for get_all_function_names
def test_get_all_function_names_with_valid_code() -> None:
    code = """
def foo():
    pass

async def bar():
    pass
"""
    success, function_names = get_all_function_names(code)
    assert success is True
    assert function_names == ["foo", "bar"]


def test_get_all_function_names_with_syntax_error(caplog) -> None:
    code = """
def foo():
    pass

async def bar():
    pass

invalid syntax
"""
    success, function_names = get_all_function_names(code)
    assert success is False
    assert function_names == []
    assert "Syntax error in code" in caplog.text


def test_get_all_function_names_with_no_functions() -> None:
    code = """
x = 1
y = 2
"""
    success, function_names = get_all_function_names(code)
    assert success is True
    assert function_names == []


def test_get_all_function_names_with_nested_functions() -> None:
    code = """
def outer():
    def inner():
        pass
    return inner
"""
    success, function_names = get_all_function_names(code)
    assert success is True
    assert function_names == ["outer", "inner"]


# tests for get_run_tmp_file
def test_get_run_tmp_file_creates_temp_directory() -> None:
    file_path = Path("test_file.py")
    tmp_file_path = get_run_tmp_file(file_path)

    assert tmp_file_path.name == "test_file.py"
    assert tmp_file_path.parent.name.startswith("codeflash_")
    assert tmp_file_path.parent.exists()


def test_get_run_tmp_file_reuses_temp_directory() -> None:
    file_path1 = Path("test_file1.py")
    file_path2 = Path("test_file2.py")

    tmp_file_path1 = get_run_tmp_file(file_path1)
    tmp_file_path2 = get_run_tmp_file(file_path2)

    assert tmp_file_path1.parent == tmp_file_path2.parent
    assert tmp_file_path1.name == "test_file1.py"
    assert tmp_file_path2.name == "test_file2.py"
    assert tmp_file_path1.parent.name.startswith("codeflash_")
    assert tmp_file_path1.parent.exists()


# tests for path_belongs_to_site_packages
def test_path_belongs_to_site_packages_with_site_package_path(monkeypatch) -> None:
    site_packages = [Path("/usr/local/lib/python3.9/site-packages")]
    monkeypatch.setattr(site, "getsitepackages", lambda: site_packages)

    file_path = Path("/usr/local/lib/python3.9/site-packages/some_package")
    assert path_belongs_to_site_packages(file_path) is True


def test_path_belongs_to_site_packages_with_non_site_package_path(monkeypatch) -> None:
    site_packages = [Path("/usr/local/lib/python3.9/site-packages")]
    monkeypatch.setattr(site, "getsitepackages", lambda: site_packages)

    file_path = Path("/usr/local/lib/python3.9/other_directory/some_package")
    assert path_belongs_to_site_packages(file_path) is False


def test_path_belongs_to_site_packages_with_relative_path(monkeypatch) -> None:
    site_packages = [Path("/usr/local/lib/python3.9/site-packages")]
    monkeypatch.setattr(site, "getsitepackages", lambda: site_packages)

    file_path = Path("some_package")
    assert path_belongs_to_site_packages(file_path) is False


# tests for is_class_defined_in_file
def test_is_class_defined_in_file_with_existing_class(tmp_path: Path) -> None:
    test_file = tmp_path / "test_file.py"
    test_file.write_text("""
class MyClass:
    pass
""")

    assert is_class_defined_in_file("MyClass", test_file) is True


def test_is_class_defined_in_file_with_non_existing_class(tmp_path: Path) -> None:
    test_file = tmp_path / "test_file.py"
    test_file.write_text("""
class MyClass:
    pass
""")

    assert is_class_defined_in_file("OtherClass", test_file) is False


def test_is_class_defined_in_file_with_no_classes(tmp_path: Path) -> None:
    test_file = tmp_path / "test_file.py"
    test_file.write_text("""
def my_function():
    pass
""")

    assert is_class_defined_in_file("MyClass", test_file) is False


def test_is_class_defined_in_file_with_non_existing_file() -> None:
    non_existing_file = Path("/non/existing/file.py")

    assert is_class_defined_in_file("MyClass", non_existing_file) is False
