#!/usr/bin/env python3
import os
import sqlite3
from collections import OrderedDict
from typing import List

from remember.command_store_lib import get_file_path
from remember.handle_args import setup_args_for_setup

HISTORY_FILE = 'HISTFILE={}\n'
HOOK_STRING = '# Remember command hook'
HOOK_FUNCTION = """hook_function() {{
  last_line=$(tail -1 {})
  pwdresult=$(pwd)
  echo "$pwdresult<<!>>$last_line" >> ~/.histcontext
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

ALIASES = """
alias re='python3 {remember_home}/remember_main.py {save_dir} ~/.histcontext'
alias lh='python3 {remember_home}/local_history.py {save_dir} ~/.histcontext -q'
alias rex='python3 {remember_home}/execute_last.py {save_dir} {history_file}'
alias rt='python3 {remember_home}/remember_main.py {save_dir} ~/.histcontext -m 10'
alias rei='python3 {remember_home}/remember_main.py -e {save_dir} ~/.histcontex'
alias rti='python3 {remember_home}/remember_main.py -e {save_dir} ~/.histcontext -m 10'
alias ure='python3 {remember_home}/update_store.py {save_dir}'
alias gen='python3 {remember_home}/generate_store.py ~/.histcontext {save_dir}'
"""


def main() -> None:

    # The keys are what to check for in the rc file the values are what to write
    # if the key isn't present
    check_write_dict = OrderedDict()
    check_write_dict['HISTSIZE'] = 'HISTSIZE=50000\n'
    check_write_dict['SAVEHIST'] = 'SAVEHIST=50000\n'
    check_write_dict['HISTFILESIZE'] = 'HISTFILESIZE=50000\n'

    args = setup_args_for_setup()
    check_write_dict['HISTFILE'] = HISTORY_FILE.format(args.history_file_path)
    remember_home = args.remember3_dir
    save_dir = args.save_dir
    history_file = args.history_file_path
    alias_lines = ALIASES.format(
        remember_home=remember_home, save_dir=save_dir, history_file=history_file).split('\n')
    alias_dict = get_alias_dict(alias_lines)
    if not ask_user_bash_or_zsh(args.history_file_path, check_write_dict):
        return
    lines_to_append = []
    if os.path.exists(args.rc_file):
        with open(args.rc_file, 'r') as rc_file:
            rc_file_lines = rc_file.readlines()
            lines_to_append.extend(check_rc_file(rc_file_lines, check_write_dict))
            lines_to_append.extend(check_rc_file(rc_file_lines, alias_dict))
    else:
        lines_to_append.extend([x for x in check_write_dict.values()])
        lines_to_append.extend([x for x in alias_dict.values()])

    if is_ok_to_append(lines_to_append, args.rc_file):
        write_lines_to_file(args.rc_file, ''.join(lines_to_append))
        create_db_if_doesnt_exist(save_dir)


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
    with open(rc_file_path, 'a') as rc_file:
        rc_file.write(lines_to_append)


def create_db_if_doesnt_exist(save_dir: str) -> None:
    store_file_path = get_file_path(save_dir)
    conn = sqlite3.connect(store_file_path)
    conn.close()


def ask_user_bash_or_zsh(history_path: str, check_write_dict: OrderedDict) -> bool:
    print("You need to be using bash or zsh. If you not using zsh I'm going to assume bash.")
    is_zsh = input("Are you using zsh [y or n or [e]xit]: ")
    if is_zsh == 'n' or is_zsh == 'y':
        if is_zsh == 'y':
            check_write_dict['setopt INC_APPEND_HISTORY'] = 'setopt INC_APPEND_HISTORY\n'
        check_write_dict[HOOK_STRING] = create_hook(is_zsh == 'y', history_path)
        return True
    else:
        print("I didn't do anything.")
        return False


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


if __name__ == "__main__":
    main()
