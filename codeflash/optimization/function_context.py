import ast
import logging
import os
from typing import NoReturn

import jedi
import tiktoken
from jedi.api.classes import Name
from pydantic.dataclasses import dataclass

from codeflash.code_utils.code_extractor import get_code_no_skeleton, get_code
from codeflash.code_utils.code_utils import path_belongs_to_site_packages
from codeflash.discovery.functions_to_optimize import FunctionToOptimize, FunctionParent


def belongs_to_class(name: Name, class_name: str) -> bool:
    """
    Check if the given name belongs to the specified class.
    """
    if name.full_name and name.full_name.startswith(name.module_name):
        subname = name.full_name[len(name.module_name) + 1 :]
        class_prefix = f"{class_name}."
        return subname.startswith(class_prefix)
    return False


def belongs_to_function(name: Name, function_name: str) -> bool:
    """
    Check if the given name belongs to the specified function
    """
    if name.full_name and name.full_name.startswith(name.module_name):
        subname = name.full_name.replace(name.module_name, "", 1)
    else:
        return False
    # The name is defined inside the function or is the function itself
    return f".{function_name}." in subname or f".{function_name}" == subname


@dataclass(frozen=True, config={"arbitrary_types_allowed": True})
class Source:
    full_name: str
    definition: Name
    source_code: str


def get_type_annotation_context(
    function: FunctionToOptimize, jedi_script: jedi.Script, project_root_path: str
) -> list[tuple[Source, str, str]]:
    function_name: str = function.function_name
    file_path: str = function.file_path
    with open(file_path, "r", encoding="utf8") as file:
        file_contents: str = file.read()
    module: ast.Module = ast.parse(file_contents)
    sources: list[tuple[Source, str, str]] = []
    ast_parents: list[str] = []

    def visit_children(
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module, node_parents
    ) -> NoReturn:
        for child in ast.iter_child_nodes(node):
            visit(child, node_parents)

    def visit(
        node: ast.AST | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module,
        node_parents: list[FunctionParent | str],
    ) -> NoReturn:
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name and node_parents == function.parents:
                    for arg in node.args.args:
                        if arg.annotation and hasattr(arg.annotation, "id"):
                            name = arg.annotation.id
                            line_no = arg.annotation.lineno
                            col_no = arg.annotation.col_offset
                            try:
                                definition: list[Name] = jedi_script.goto(
                                    line=line_no,
                                    column=col_no,
                                    follow_imports=True,
                                    follow_builtin_imports=False,
                                )
                            except Exception as e:
                                logging.error(
                                    f"Error while getting definition for {name.full_name}: {e}"
                                )
                                definition = []
                            if definition:  # TODO can be multiple definitions
                                definition_path = str(definition[0].module_path)
                                # The definition is part of this project and not defined within the original function
                                if (
                                    definition_path.startswith(project_root_path + os.sep)
                                    and definition[0].full_name
                                    and not path_belongs_to_site_packages(definition_path)
                                    and not belongs_to_function(definition[0], function_name)
                                ):
                                    source_code = get_code(
                                        FunctionToOptimize(
                                            definition[0].name,
                                            definition_path,
                                            node_parents[:-1],
                                        )
                                    )
                                    if source_code:
                                        sources.append(
                                            (
                                                Source(
                                                    definition[0].name,
                                                    definition[0],
                                                    source_code,
                                                ),
                                                definition_path,
                                                definition[0].full_name.removeprefix(
                                                    definition[0].module_name + "."
                                                ),
                                            )
                                        )
            if not isinstance(node, ast.Module):
                node_parents.append(node.name)
            visit_children(node, node_parents)
            if not isinstance(node, ast.Module):
                node_parents.pop()

    visit(module, ast_parents)

    return sources


def get_function_variables_definitions(
    function_to_optimize: FunctionToOptimize, project_root_path: str
) -> list[tuple[Source, str, str]]:
    function_name = function_to_optimize.function_name
    file_path = function_to_optimize.file_path
    script = jedi.Script(path=file_path, project=jedi.Project(path=project_root_path))
    sources: list[tuple[Source, str, str]] = []
    # TODO: The function name condition can be stricter so that it does not clash with other class names etc.
    # TODO: The function could have been imported as some other name,
    #  we should be checking for the translation as well. Also check for the original function name.
    names = []
    for ref in script.get_names(all_scopes=True, definitions=False, references=True):
        if ref.full_name:
            if function_to_optimize.parents:
                # Check if the reference belongs to the specified class when FunctionParent is provided
                if belongs_to_class(
                    ref, function_to_optimize.parents[-1].name
                ) and belongs_to_function(ref, function_name):
                    names.append(ref)
            else:
                if belongs_to_function(ref, function_name):
                    names.append(ref)

    for name in names:
        try:
            definitions: list[Name] = script.goto(
                line=name.line,
                column=name.column,
                follow_imports=True,
                follow_builtin_imports=False,
            )
        except Exception as e:
            try:
                logging.error(f"Error while getting definition for {name.full_name}: {e}")
            except Exception as e:
                # name.full_name can also throw exceptions sometimes
                logging.error(f"Error while getting definition: {e}")
            definitions = []
        if definitions:
            # TODO: there can be multiple definitions, see how to handle such cases
            definition_path = str(definitions[0].module_path)
            # The definition is part of this project and not defined within the original function
            if (
                definition_path.startswith(project_root_path + os.sep)
                and not path_belongs_to_site_packages(definition_path)
                and definitions[0].full_name
                and not belongs_to_function(definitions[0], function_name)
            ):
                source_code = get_code_no_skeleton(definition_path, definitions[0].name)
                if source_code:
                    sources.append(
                        (
                            Source(name.full_name, definitions[0], source_code),
                            definition_path,
                            name.full_name.removeprefix(name.module_name + "."),
                        )
                    )
    annotation_sources = get_type_annotation_context(
        function_to_optimize, script, project_root_path
    )
    sources[:0] = annotation_sources  # prepend the annotation sources
    deduped_sources = []
    existing_full_names = set()
    for source in sources:
        if source[0].full_name not in existing_full_names:
            deduped_sources.append(source)
            existing_full_names.add(source[0].full_name)
    return deduped_sources


MAX_PROMPT_TOKENS = 4096  # 128000  # gpt-4-128k


def get_constrained_function_context_and_dependent_functions(
    function_to_optimize: FunctionToOptimize,
    project_root_path: str,
    code_to_optimize: str,
    max_tokens: int = MAX_PROMPT_TOKENS,
) -> tuple[str, list[tuple[Source, str, str]]]:
    # TODO: Not just do static analysis, but also find the datatypes of function arguments by running the existing
    #  unittests and inspecting the arguments to resolve the real definitions and dependencies.
    dependent_functions: list[tuple[Source, str, str]] = get_function_variables_definitions(
        function_to_optimize, project_root_path
    )
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    code_to_optimize_tokens = tokenizer.encode(code_to_optimize)
    dependent_functions_sources = [function[0].source_code for function in dependent_functions]
    dependent_functions_tokens = [
        len(tokenizer.encode(function)) for function in dependent_functions_sources
    ]
    context_list = []
    context_len = len(code_to_optimize_tokens)
    logging.debug(f"ORIGINAL CODE TOKENS LENGTH: {context_len}")
    logging.debug(f"ALL DEPENDENCIES TOKENS LENGTH: {sum(dependent_functions_tokens)}")
    for function_source, source_len in zip(dependent_functions_sources, dependent_functions_tokens):
        if context_len + source_len <= max_tokens:
            context_list.append(function_source)
            context_len += source_len
        else:
            break
    logging.debug("FINAL OPTIMIZATION CONTEXT TOKENS LENGTH:", context_len)
    return "\n".join(context_list) + "\n" + code_to_optimize, dependent_functions
