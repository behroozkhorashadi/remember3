"""
This Module contains the core logic for the remember functions.
"""
import os.path
from enum import Enum
from typing import List, Optional

from remember.sql_store import SqlCommandStore, IgnoreRules, Command

import shutil
import time


PROCESSED_TO_TAG = '****** previous commands read *******'
CUSTOM_HIST_HEAD = '## remember command custom history file ##\n'
CUSTOM_HIST_SEPARATOR = '<<!>>'
REMEMBER_DB_FILE_NAME = 'remember.db'
DEFAULT_LAST_SAVE_FILE_NAME = 'last_saved_results.txt'
IGNORE_RULE_FILE_NAME = 'ignore_rules.txt'


class BColors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CommandAndContext(object):
    def __init__(self, command_line: str, directory_context: str=None):
        self._command_line = command_line
        self._directory_context = directory_context

    def command_line(self) -> str:
        return self._command_line

    def directory_context(self) -> Optional[str]:
        return self._directory_context

class HistoryFileType(Enum):
    UNKNOWN = 0
    STANDARD = 1
    CUSTOM = 2



class HistoryProcessor(object):
    """This class helps process the history file into the store"""
    def __init__(self,
                 store: SqlCommandStore,
                 history_file_path: str,
                 save_directory: str,
                 threshold: int = 100):
        self._store = store
        self._threshold = threshold
        self._history_file_path = history_file_path
        tmp_file_path = os.path.join(save_directory, IGNORE_RULE_FILE_NAME)
        self._ignore_rule_file = tmp_file_path if os.path.isfile(tmp_file_path) else None
        self._history_file_type = HistoryFileType.UNKNOWN
        self._lines_processed = False

    def process_history_file(self) -> None:
        print('Reading ' + self._history_file_path)
        start_time = time.time()
        lines = get_string_file_lines(self._history_file_path)
        self._set_history_file_type(lines)
        commands = get_unread_commands(lines, self._history_file_type)
        if len(commands) > self._threshold:
            process_history_commands(self._store, commands, self._ignore_rule_file)
            print(f'Wrote to database in {time.time()-start_time} seconds')
            self._lines_processed = True

    def update_history_file(self) -> None:
        if not self._lines_processed:
            return
        if self._history_file_type == HistoryFileType.STANDARD:
            with open(self._history_file_path, "a") as myfile:
                myfile.write(f'{PROCESSED_TO_TAG}\n')
        else:
            with open(self._history_file_path, 'w') as hist_file:
                hist_file.write(CUSTOM_HIST_HEAD)

    def _set_history_file_type(self, history_lines: List[str]):
        if history_lines[0] == CUSTOM_HIST_HEAD:
            self._history_file_type = HistoryFileType.CUSTOM
            return
        self._history_file_type = HistoryFileType.STANDARD


def create_ignore_rule(src_file: str) -> IgnoreRules:
    """Generate a IgnoreRules object from the input file."""
    ignore_rules = IgnoreRules()
    methods = {
        's': ignore_rules.add_starts_with,
        'c': ignore_rules.add_contains,
        'm': ignore_rules.add_matches,
    }
    if not os.path.isfile(src_file):
        return ignore_rules
    for line in open(src_file).readlines():
        split = line.split(":", 1)
        if len(split) == 2:
            methods[split[0]](split[1].strip())
    return ignore_rules


def print_commands(commands: List[Command], highlighted_terms: Optional[List] = None) -> None:
    """Pretty print the commands."""
    if highlighted_terms is None:
        highlighted_terms = []
    x = 1
    for command in commands:
        print_command(x, command, highlighted_terms)
        x = x + 1


def print_command(index: int, command: Command,
                  highlighted_terms: Optional[List[str]] = None) -> None:
    """Pretty print a single command."""
    if highlighted_terms is None:
        highlighted_terms = []
    command_str = command.get_unique_command_id()
    info_str = command.get_command_info()
    for term in highlighted_terms:
        command_str = _highlight_term_in_string(command_str, term)
        info_str = _highlight_term_in_string(info_str, term)
    print(_create_indexed_highlighted_print_string(index, command_str, command))
    if info_str:
        print(BColors.FAIL + "Command context/info: " + info_str + BColors.ENDC)


def _highlight_term_in_string(highlight_str: str, term: str) -> str:
    return highlight_str.replace(term, f'{BColors.OKGREEN}{term}{BColors.YELLOW}')


def _create_indexed_highlighted_print_string(index: int, command_str: str, command: Command) -> str:
    return f'{BColors.HEADER}({index}): {BColors.YELLOW}{command_str}{BColors.OKBLUE} ' \
           f'--count:{command.get_count_seen()}{BColors.ENDC}'


# def get_last_n_lines(file_name: str, max_read_lines: int = -1) -> List[str]:
#     #TODO use this method instead of the less efficient one that read the whole file.
#     # Create an empty list to keep the track of last N lines
#     list_of_lines = []
#     # Open file for reading in binary mode
#     with open(file_name, 'rb') as read_obj:
#         # Move the cursor to the end of the file
#         read_obj.seek(0, os.SEEK_END)
#         # Create a buffer to keep the last read line
#         buffer = bytearray()
#         # Get the current position of pointer i.e eof
#         pointer_location = read_obj.tell()
#         # Loop till pointer reaches the top of the file
#         while pointer_location >= 0:
#             # Move the file pointer to the location pointed by pointer_location
#             read_obj.seek(pointer_location)
#             # Shift pointer location by -1
#             pointer_location = pointer_location -1
#             # read that byte / character
#             new_byte = read_obj.read(1)
#             # If the read byte is new line character then it means one line is read
#             if new_byte == b'\n':
#                 # Save the line in list of lines
#                 last_read_line = buffer.decode()[::-1]
#                 if PROCESSED_TO_TAG in last_read_line:
#                     return list(reversed(list_of_lines))
#                 list_of_lines.append(buffer.decode()[::-1])
#                 # If the size of list reaches N, then return the reversed list
#                 if max_read_lines != -1 and len(list_of_lines) == max_read_lines:
#                     return list(reversed(list_of_lines))
#                 # Reinitialize the byte array to save next line
#                 buffer = bytearray()
#             else:
#                 # If last read character is not eol then add it in buffer
#                 buffer.extend(new_byte)
#
#         # As file is read completely, if there is still data in buffer, then its first line.
#         if len(buffer) > 0:
#             list_of_lines.append(buffer.decode()[::-1])
#
#     # return the reversed list
#     return list(reversed(list_of_lines))

def get_string_file_lines(src_file: str) -> List[str]:
    unprocessed_lines: List = []
    tmp_hist_file = src_file + '.tmp'
    shutil.copyfile(src_file, tmp_hist_file)
    history_lines = open(tmp_hist_file, 'rb').readlines()
    for line in history_lines:
        line_str = _try_decode_line(line)
        if line_str:
            unprocessed_lines.append(line_str)
    os.remove(tmp_hist_file)
    return unprocessed_lines


def get_unread_commands(history_lines: List[str],
                        file_type: HistoryFileType) -> List[CommandAndContext]:
    assert(file_type != HistoryFileType.UNKNOWN)
    """Read the history file and get all the unread commands."""
    unprocessed_commands: List[CommandAndContext] = []
    if file_type == HistoryFileType.CUSTOM:
        return _get_unread_commands_custom_file(history_lines[1:])
    for line in reversed(history_lines):
        if PROCESSED_TO_TAG in line:
            return list(reversed(unprocessed_commands))
        unprocessed_commands.append(CommandAndContext(line.strip()))
    return unprocessed_commands


def _try_decode_line(line: bytes) -> Optional[str]:
    try:
        return line.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _get_unread_commands_custom_file(file_lines: List[str]) -> List[CommandAndContext]:
    return [CommandAndContext(y[1].strip(), y[0]) for y in
            [x.split(CUSTOM_HIST_SEPARATOR) for x in file_lines]]


def process_history_commands(
        store: SqlCommandStore,
        commands: List[CommandAndContext],
        ignore_file: Optional[str] = None) -> None:
    """Process the commands from the history file."""

    output = []
    if ignore_file:
        ignore_rules = create_ignore_rule(ignore_file)
    else:
        ignore_rules = IgnoreRules()
    # get the max count
    current_time = time.time()
    for command_and_context in commands:
        current_time += 1
        command = Command(command_str=command_and_context.command_line(),
                          last_used=current_time,
                          directory_context=command_and_context.directory_context())
        if ignore_rules.is_match(command.get_unique_command_id()):
            continue
        store.add_command(command)
        output.append(command.get_unique_command_id())


def get_file_path(directory_path: str) -> str:
    """Get the sql db file given the directory where the files is."""
    return os.path.join(directory_path, REMEMBER_DB_FILE_NAME)


def load_command_store(db_file_name: str) -> SqlCommandStore:
    """Get the sql command store from the input file."""
    if not os.path.exists(db_file_name):
        raise Exception(f'db file: {db_file_name} does not exist')
    return SqlCommandStore(db_file_name)


def save_last_search(file_path: str, last_search_result: List[Command]) -> None:
    if len(last_search_result) == 0:
        return
    with open(file_path, 'w') as file_handler:
        for search_command in last_search_result:
            file_handler.write('%s\n' % search_command.get_unique_command_id())


def read_last_search(file_path: str) -> List[str]:
    with open(file_path) as read_file:
        return [x.strip() for x in read_file.readlines()]


def generate_store_from_args(history_file_path: str, save_directory: str) -> None:
    store = load_command_store(get_file_path(save_directory))
    start_history_processing(store, history_file_path, save_directory, 1)

def start_history_processing(
        store: SqlCommandStore,
        history_file_path: str,
        save_directory: str,
        threshold: int = 100) -> None:
    history_processor = HistoryProcessor(store, history_file_path, save_directory, threshold)
    history_processor.process_history_file()
    history_processor.update_history_file()
