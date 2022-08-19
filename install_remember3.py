#!/usr/bin/env python3
from argparse import Namespace
from dataclasses import dataclass
import os
import pathlib
import shutil
import sqlite3
from collections import OrderedDict
from tkinter import filedialog as fd
from typing import List, Optional, Tuple

from remember.command_store_lib import get_file_path, CUSTOM_HIST_HEAD
from remember.handle_args import setup_args_for_setup
from remember.constants import ALIASES, CUSTOM_HISTORY_FILE_PATH, DEFAULT_REMEMBER_SAVE_DIR


HISTORY_FILE_PATH = os.getenv('HISTFILE')
HISTORY_FILE = 'HISTFILE={}\n'
HOOK_STRING = '# Remember command hook'
HOOK_FUNCTION = """hook_function() {{
  last_line=$(tail -1 {})
  pwdresult=$(pwd)
  echo "$pwdresult<<!>>$last_line" >> ~/.remember3/.histcontext
}}"""

ZSH_REMEMBER_HOOK = """
{hook_str}
autoload -U add-zsh-hook
{hook_func}
add-zsh-hook precmd hook_function\n
"""

BASH_REMEMBER_HOOK = """
{hook_str}
shopt -s histappend
if ! echo "$PROMPT_COMMAND" | grep 'history -a'; then
   export PROMPT_COMMAND="history -a;$PROMPT_COMMAND"
fi

# If PC contains anything, add semicolon and space
{hook_func}
# Add custom PC
if ! echo "$PROMPT_COMMAND" | grep 'hook_function'; then
  export PROMPT_COMMAND='hook_function;'$PROMPT_COMMAND
fi

"""


@dataclass
class SetupArgs:
    is_zsh: bool
    save_dir_path: str
    history_file_path: str
    rc_file_path: str


def main() -> None:
    args = setup_args_for_setup()
    setup_args = setup_all_files_and_dirs(args)
    if not setup_args:
        return
    is_zsh = setup_args.is_zsh
    history_file_path = setup_args.history_file_path
    save_dir = setup_args.save_dir_path
    rc_file_path = setup_args.rc_file_path
    alias_dict, check_write_dict = create_lines_to_write(is_zsh, history_file_path, save_dir)
    write_lines_to_files(rc_file_path, save_dir, check_write_dict, alias_dict)


def setup_all_files_and_dirs(args: Namespace) -> Optional[SetupArgs]:
    is_zsh = _ask_user_is_zsh()
    if is_zsh is None:
        return None
    history_file_path = _get_history_file_path(is_zsh)
    print(history_file_path)
    if not history_file_path:
        return None
    rc_file_path = _return_rc_file_path(is_zsh, args.rc_file)
    if not rc_file_path:
        print("Counldn't find your RC file, please add it as an arg.")
        return None
    print(rc_file_path)
    save_dir = _create_remember_save_dir()
    print(f"save dir is {save_dir}")
    _import_remember_files(save_dir)
    return SetupArgs(is_zsh, save_dir, history_file_path, rc_file_path)


def create_lines_to_write(
        is_zsh: bool, history_file_path: str, save_dir) -> Tuple[OrderedDict, OrderedDict]:
    remember_home = pathlib.Path(__file__).parent.resolve()
    # The keys are what to check for in the rc file the values are what to write
    # if the key isn't present
    check_write_dict = OrderedDict()
    check_write_dict['HISTSIZE'] = 'HISTSIZE=50000\n'
    check_write_dict['SAVEHIST'] = 'SAVEHIST=50000\n'
    check_write_dict['HISTFILESIZE'] = 'HISTFILESIZE=50000\n'
    _append_rc_file_options(is_zsh, history_file_path, check_write_dict)
    check_write_dict['HISTFILE'] = HISTORY_FILE.format(history_file_path)
    alias_lines = ALIASES.format(remember_home=remember_home, save_dir=save_dir).split('\n')
    alias_dict = get_alias_dict(alias_lines)
    return alias_dict, check_write_dict


def write_lines_to_files(
        rc_file_path: str,
        save_dir: str,
        check_write_dict: OrderedDict,
        alias_dict: OrderedDict) -> None:
    lines_to_append = []
    if os.path.exists(rc_file_path):
        with open(rc_file_path, 'r', encoding="utf8") as rc_file:
            rc_file_lines = rc_file.readlines()
            lines_to_append.extend(check_rc_file(rc_file_lines, check_write_dict))
            lines_to_append.extend(check_rc_file(rc_file_lines, alias_dict))
    else:
        lines_to_append.extend(list(check_write_dict.values()))
        lines_to_append.extend(list(alias_dict.values()))

    if is_ok_to_append(lines_to_append, rc_file_path):
        write_lines_to_file(rc_file_path, ''.join(lines_to_append))
        create_db_if_doesnt_exist(save_dir)
    write_lines_to_file(CUSTOM_HISTORY_FILE_PATH, CUSTOM_HIST_HEAD)


def is_ok_to_append(lines_to_append: List[str], rc_file_path: str) -> bool:
    for line in lines_to_append:
        print(line)
    user_response = input(f'Ok to add the following lines to {rc_file_path}? [y|n]: ')
    return user_response == 'y'


def get_alias_dict(alias_lines: List[str]) -> OrderedDict:
    alias_write_dict = OrderedDict()
    for line in alias_lines:
        split_equals = line.split('=')
        alias_write_dict[split_equals[0]] = line + '\n'
    return alias_write_dict


def write_lines_to_file(rc_file_path: str, lines_to_append: str) -> None:
    if len(lines_to_append) == 0 or not is_ok_to_append(lines_to_append.split('\n'), rc_file_path):
        return
    with open(rc_file_path, 'a', encoding="utf8") as rc_file:
        rc_file.write(lines_to_append)


def create_db_if_doesnt_exist(save_dir: str) -> None:
    store_file_path = get_file_path(save_dir)
    conn = sqlite3.connect(store_file_path)
    conn.close()


def _append_rc_file_options(is_zsh: bool, history_path: str, check_write_dict: OrderedDict) -> None:
    if is_zsh:
        check_write_dict['setopt INC_APPEND_HISTORY'] = 'setopt INC_APPEND_HISTORY\n'
    check_write_dict[HOOK_STRING] = create_hook(is_zsh, history_path)


def create_hook(is_zsh: bool, history_file_path: str) -> str:
    hook_function = HOOK_FUNCTION.format(history_file_path)
    if is_zsh:
        return ZSH_REMEMBER_HOOK.format(hook_str=HOOK_STRING, hook_func=hook_function)
    return BASH_REMEMBER_HOOK.format(hook_str=HOOK_STRING, hook_func=hook_function)


def check_rc_file(lines: List[str], check_write_dict: OrderedDict) -> List[str]:
    lines_to_append = []
    for key, value in check_write_dict.items():
        if not any(key in line for line in lines):
            lines_to_append.append(value)
    return lines_to_append


def _return_rc_file_path(is_zsh: bool, rc_arg_val: str) -> Optional[str]:
    rc_path = "~/.zshrc" if is_zsh else "~/.bashrc"
    expanded_path = os.path.expanduser(rc_path)
    if os.path.exists(expanded_path):
        return expanded_path
    return rc_arg_val


def _get_history_file_path(is_zsh: bool) -> Optional[str]:
    default_history_file_path = "~/.histfile" if is_zsh else "~/.bash_history"
    expanded_path = os.path.expanduser(default_history_file_path)
    if not HISTORY_FILE_PATH and os.path.exists(expanded_path):
        return expanded_path
    return None


def _ask_user_is_zsh() -> Optional[bool]:
    print("You need to be using bash or zsh. If you not using zsh I'm going to assume bash.")
    is_zsh_str = input("Are you using zsh [y or n or [e]xit]: ")
    if is_zsh_str in ('n', 'y'):
        return is_zsh_str == 'y'
    return None


def _create_remember_save_dir() -> str:
    if not os.path.exists(DEFAULT_REMEMBER_SAVE_DIR):
        os.mkdir(DEFAULT_REMEMBER_SAVE_DIR)
    return DEFAULT_REMEMBER_SAVE_DIR


def _import_remember_files(save_dir_path: str) -> None:
    if _is_answer_yes("Do you have a remember db file to import?"):
        import_db_file_path = fd.askopenfilename(filetypes=[("Database files", "*.db")])
        db_new_location = os.path.join(save_dir_path, os.path.basename(import_db_file_path))
        db_file_exists = os.path.exists(db_new_location)
        if not db_file_exists or (db_file_exists and _is_answer_yes("Delete existing db file?")):
            if db_file_exists:
                os.remove(db_new_location)
            shutil.copyfile(import_db_file_path, db_new_location)
            print(db_new_location)
    if _is_answer_yes("Do you have a remember ignore file to import"):
        import_ignore_file_path = fd.askopenfilename(filetypes=[("Text files", "*.txt")])
        ignore_new_location = os.path.join(save_dir_path, os.path.basename(import_ignore_file_path))
        ignore_file_exists = os.path.exists(ignore_new_location)
        if (not ignore_file_exists
                or (ignore_file_exists and _is_answer_yes("Delete existing ignore file?"))):
            if ignore_file_exists:
                os.remove(ignore_new_location)
            shutil.copyfile(import_ignore_file_path, ignore_new_location)
            print(ignore_new_location)


def _is_answer_yes(question: str) -> bool:
    yes_no_answer = input(f"{question} [y|n]: ")
    return yes_no_answer in ('y', 'yes')


if __name__ == "__main__":
    main()
