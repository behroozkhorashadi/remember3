import os

DEFAULT_REMEMBER_SAVE_DIR = os.path.expanduser("~/.remember3")
CUSTOM_HISTORY_FILE_PATH = os.path.join(DEFAULT_REMEMBER_SAVE_DIR, '.histfile')

ALIASES = """
alias re='python3 {remember_home}/remember_main.py {save_dir}'
alias lh='python3 {remember_home}/local_history.py -q'
alias rex='python3 {remember_home}/execute_last.py'
alias rei='python3 {remember_home}/remember_main.py -e {save_dir}'
alias ure='python3 {remember_home}/update_store.py {save_dir}'
"""
