from __future__ import annotations

import sys
import time
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import git
import inquirer
from unidiff import PatchSet

from codeflash.cli_cmds.cli_common import inquirer_wrapper
from codeflash.cli_cmds.console import logger

if TYPE_CHECKING:
    from git import Repo


def get_git_diff(
    repo_directory: Path = Path.cwd(),
    uncommitted_changes: bool = False,
) -> dict[str, list[int]]:
    repository = git.Repo(repo_directory, search_parent_directories=True)
    commit = repository.head.commit
    if uncommitted_changes:
        uni_diff_text = repository.git.diff(
            None,
            "HEAD",
            ignore_blank_lines=True,
            ignore_space_at_eol=True,
        )
    else:
        uni_diff_text = repository.git.diff(
            commit.hexsha + "^1",
            commit.hexsha,
            ignore_blank_lines=True,
            ignore_space_at_eol=True,
        )
    patch_set = PatchSet(StringIO(uni_diff_text))
    change_list: dict[str, list[int]] = {}  # list of changes
    for patched_file in patch_set:
        file_path: Path = Path(patched_file.path)
        if file_path.suffix != ".py":
            continue
        file_path = Path(repository.working_dir) / file_path
        logger.debug(f"file name: {file_path}")

        add_line_no: list[int] = [
            line.target_line_no
            for hunk in patched_file
            for line in hunk
            if line.is_added and line.value.strip() != ""
        ]  # the row number of deleted lines

        logger.debug(f"added lines: {add_line_no}")

        del_line_no: list[int] = [
            line.source_line_no
            for hunk in patched_file
            for line in hunk
            if line.is_removed and line.value.strip() != ""
        ]  # the row number of added lines

        logger.debug(f"deleted lines: {del_line_no}")

        change_list[file_path] = add_line_no
    return change_list


def get_current_branch(repo: Repo | None = None) -> str:
    """Returns the name of the current branch in the given repository.

    :param repo: An optional Repo object. If not provided, the function will
                 search for a repository in the current and parent directories.
    :return: The name of the current branch.
    """
    repository: Repo = repo if repo else git.Repo(search_parent_directories=True)
    return repository.active_branch.name


def get_remote_url(repo: Repo | None = None) -> str:
    repository: Repo = repo if repo else git.Repo(search_parent_directories=True)
    return repository.remote().url


def get_repo_owner_and_name(repo: Repo | None = None) -> tuple[str, str]:
    remote_url = get_remote_url(repo)  # call only once
    remote_url = get_remote_url(repo).removesuffix(".git") if remote_url.endswith(".git") else remote_url
    split_url = remote_url.split("/")
    repo_owner_with_github, repo_name = split_url[-2], split_url[-1]
    repo_owner = (
        repo_owner_with_github.split(":")[1] if ":" in repo_owner_with_github else repo_owner_with_github
    )
    return repo_owner, repo_name


def git_root_dir(repo: Repo | None = None) -> Path:
    repository: Repo = repo if repo else git.Repo(search_parent_directories=True)
    return Path(repository.working_dir)


def check_running_in_git_repo(module_root: str) -> bool:
    try:
        _ = git.Repo(module_root, search_parent_directories=True).git_dir
    except git.InvalidGitRepositoryError:
        return confirm_proceeding_with_no_git_repo()
    else:
        return True


def confirm_proceeding_with_no_git_repo() -> str | bool:
    return (
        inquirer_wrapper(
            inquirer.confirm,
            message="WARNING: I did not find a git repository for your code. If you proceed in running codeflash, optimized code will"
            " be written over your current code and you could irreversibly lose your current code. Proceed?",
            default=False,
        )
        if sys.__stdin__ is not None and sys.__stdin__.isatty()
        else True
    )


def check_and_push_branch(repo: git.Repo, wait_for_push: bool = False) -> bool:
    current_branch = repo.active_branch.name
    origin = repo.remote(name="origin")

    # Check if the branch is pushed
    if f"origin/{current_branch}" not in repo.refs:
        logger.warning(f"⚠️ The branch '{current_branch}' is not pushed to the remote repository.")
        if not sys.__stdin__.isatty():
            logger.warning("Non-interactive shell detected. Branch will not be pushed.")
            return False
        if sys.__stdin__.isatty() and inquirer_wrapper(
            inquirer.confirm,
            message=f"⚡️ In order for me to create PRs, your current branch needs to be pushed. Do you want to push the branch "
            f"'{current_branch}' to the remote repository?",
            default=False,
        ):
            origin.push(current_branch)
            logger.info(f"⬆️ Branch '{current_branch}' has been pushed to origin.")
            if wait_for_push:
                time.sleep(3)  # adding this to give time for the push to register with GitHub,
                # so that our modifications to it are not rejected
            return True
        logger.info(f"🔘 Branch '{current_branch}' has not been pushed to origin.")
        return False
    logger.debug(f"The branch '{current_branch}' is present in the remote repository.")
    return True
