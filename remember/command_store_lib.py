"""
This Module contains the core logic for the remember functions.
"""
import sqlite3
import os.path
from typing import List, Optional, Set

from remember.sql_query_constants import SQL_CREATE_REMEMBER_TABLE, SEARCH_COMMANDS_QUERY, \
    SIMPLE_SELECT_COMMAND_QUERY, DELETE_FROM_REMEMBER, GET_ROWID_FOR_COMMAND, \
    INSERT_INTO_REMEMBER_QUERY, UPDATE_COUNT_QUERY, TABLE_EXISTS_QUERY, TABLE_NAME

import re
import shutil
import time

PROCESSED_TO_TAG = '****** previous commands read *******'
FILE_STORE_NAME = 'command_storage.txt'
REMEMBER_DB_FILE_NAME = 'remember.db'
DEFAULT_LAST_SAVE_FILE_NAME = 'last_saved_results.txt'
# Table type enums
JSON_STORE = 1
PICKLE_STORE = 2
SQL_STORE = 3


class bcolors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Command(object):
    """This class holds the basic pieces for a command."""

    def __init__(self, command_str: str = "", last_used: float = time.time(),
                 count_seen: int = 1):
        self._command_str = Command.get_curated_command(command_str)
        self._context_before: Set = set()
        self._context_after: Set = set()
        self._manual_comments = "Place any comments here."
        self._parse_command(self._command_str)
        self._count_seen = count_seen
        self._last_used = last_used
        self._command_info = ""

    def _parse_command(self, command: str) -> None:
        """Set the primary command."""
        command_split = command.split(" ")
        if command_split[0] == ".":
            self._primary_command = command_split[1]
            self._command_args = command_split[2:]
        else:
            self._primary_command = command_split[0]
            self._command_args = command_split[1:]

    def get_command_args(self) -> List:
        """Get the input args for the command"""
        # This is for backwards compatibility with earlier picked classes that
        # didn't have this field.
        return self._command_args

    def get_command_info(self) -> str:
        """Get the input args for the command"""
        return self._command_info

    def get_primary_command(self) -> str:
        """Get the primary command."""
        return self._primary_command

    def get_unique_command_id(self) -> str:
        """Get the commands unique id."""
        return self._command_str

    def get_count_seen(self) -> int:
        """Get the count seen."""
        return self._count_seen

    def _increment_count(self) -> None:
        """Increment the count of the command."""
        self._count_seen += 1

    def _update_time(self, updated_time: float) -> None:
        """Update the time to this new time."""
        self._last_used = updated_time

    def last_used_time(self) -> float:
        """Get the last used time in seconds from epoch"""
        return self._last_used

    def set_command_info(self, info: str) -> None:
        self._command_info = info

    @classmethod
    def get_curated_command(cls, command_str: str) -> str:
        """Given a command string curate the string and return."""
        curated_command = re.sub(' +', ' ', command_str.strip())
        if curated_command.startswith(":"):
            p = re.compile(";")
            m = p.search(curated_command)
            if m and len(curated_command) > m.start() + 1:
                curated_command = curated_command[m.start() + 1:].strip()
        return curated_command


class SqlCommandStore(object):
    def __init__(self, db_file: str = ':memory:') -> None:
        self._db_file = db_file
        self._table_creation_verified = False
        self._db_conn: Optional[sqlite3.Connection] = None

    def _get_initialized_db_connection(self) -> sqlite3.Connection:
        if not self._db_conn:
            self._db_conn = _create_db_connection(self._db_file)
            assert self._db_conn
            if not self._table_creation_verified:
                _init_tables_if_not_exists(self._db_conn)
                self._table_creation_verified = True
        return self._db_conn

    def add_command(self, command: Command) -> None:
        row_id = self._get_rowid_of_command(command.get_unique_command_id())
        db_connection = self._get_initialized_db_connection()
        with db_connection:
            cursor = db_connection.cursor()
            if row_id:
                cursor.execute(UPDATE_COUNT_QUERY, (command.last_used_time(), row_id,))
            else:
                row_insert = (command.get_unique_command_id(), command.get_count_seen(),
                              command.last_used_time(), command.get_command_info())
                cursor.execute(INSERT_INTO_REMEMBER_QUERY, row_insert)

    def _get_rowid_of_command(self, command_str: str) -> Optional[int]:
        cursor = self._get_initialized_db_connection().cursor()
        cursor.execute(GET_ROWID_FOR_COMMAND, (command_str,))
        data = cursor.fetchone()
        if data is None:
            return None
        else:
            return data[0]

    def delete_command(self, command_str: str) -> Optional[str]:
        db_conn = self._get_initialized_db_connection()
        with db_conn:
            cur = db_conn.cursor()
            cur.execute(DELETE_FROM_REMEMBER, (command_str,))
            db_conn.commit()
            if cur.rowcount == 0:
                return None
            return command_str

    def has_command(self, command: Command) -> bool:
        """This method checks to see if a command is in the store. """
        return self.has_command_by_name(command.get_unique_command_id())

    def has_command_by_name(self, command_str: str) -> bool:
        """This method checks to see if a command (by name) is in the store.
        """
        db_conn = self._get_initialized_db_connection()
        cursor = db_conn.cursor()
        cursor.execute(SIMPLE_SELECT_COMMAND_QUERY, (command_str,))
        data = cursor.fetchall()
        if len(data) == 0:
            return False
        return True

    def get_num_commands(self) -> int:
        """This method returns the number of commands in the store."""
        db_conn = self._get_initialized_db_connection()
        cursor = db_conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM {}'.format('remember'))
        count = cursor.fetchall()
        print('\nTotal rows: {}'.format(count[0][0]))
        return count[0][0]

    def search_commands(self,
                        search_terms: List,
                        starts_with: bool = False,
                        sort: bool = True,
                        search_info: bool = False) -> List:
        """This method searches the command store for the command given."""
        search_query = _create_command_search_select_query(search_terms, starts_with, sort,
                                                           search_info)
        matches = []
        db_conn = self._get_initialized_db_connection()
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(search_query)
            rows = cursor.fetchall()
            for row in rows:
                command = Command(row[0], row[2], row[1])
                command.set_command_info(row[3])
                matches.append(command)
        return matches

    def close(self) -> None:
        if self._db_conn:
            self._db_conn.close()


class IgnoreRules(object):
    """ This class holds the set of ignore rules for commands."""

    def __init__(self) -> None:
        self._start_with: List[str] = []
        self._contains: List[str] = []
        self._matches: Set = set()

    def is_match(self, command_str: str) -> bool:
        """ If the command matches any of the ignore rules returns true."""
        # ignore all empty strings.
        if not command_str:
            return True
        if command_str in self._matches:
            return True
        for val in self._start_with:
            if command_str.startswith(val):
                return True
        for val in self._contains:
            if val in command_str:
                return True
        return False

    def add_starts_with(self, command_str: str) -> None:
        """Add a starts with rule to ignore."""
        self._start_with.append(command_str)

    def add_contains(self, command_str: str) -> None:
        """Add a contains with rule to ignore."""
        self._contains.append(command_str)

    def add_matches(self, command_str: str) -> None:
        """Add a exact matches with rule to ignore."""
        self._matches.add(command_str)


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
        command_str = highlight_term_in_string(command_str, term)
        info_str = highlight_term_in_string(info_str, term)
    print(create_indexed_highlighted_print_string(index, command_str, command))
    if info_str:
        print(bcolors.FAIL + "Command context/info: " + info_str + bcolors.ENDC)


def highlight_term_in_string(highlight_str: str, term: str) -> str:
    return highlight_str.replace(term, f'{bcolors.OKGREEN}{term}{bcolors.YELLOW}')


def create_indexed_highlighted_print_string(index: int, command_str: str, command: Command) -> str:
    return f'{bcolors.HEADER}({index}): {bcolors.YELLOW}{command_str}{bcolors.OKBLUE} ' \
           f'--count:{command.get_count_seen()}{bcolors.ENDC}'


def _get_unread_commands(src_file: str) -> List:
    """Read the history file and get all the unread commands."""
    unprocessed_lines: List = []
    tmp_hist_file = src_file + '.tmp'
    shutil.copyfile(src_file, tmp_hist_file)
    try:
        for line in reversed(open(tmp_hist_file, 'rb').readlines()):
            try:
                line_str = line.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if PROCESSED_TO_TAG in line_str:
                return list(reversed(unprocessed_lines))
            unprocessed_lines.append(line_str.strip())
    finally:
        os.remove(tmp_hist_file)
    return unprocessed_lines


def read_history_file(
        store: SqlCommandStore,
        history_file_path: str,
        store_file: str,
        ignore_file: Optional[str] = None,
        mark_read: bool = True) -> None:
    """Read in the history files."""

    commands = _get_unread_commands(history_file_path)
    output = []
    if ignore_file:
        ignore_rules = create_ignore_rule(ignore_file)
    else:
        ignore_rules = IgnoreRules()
    # get the max count
    current_time = time.time()
    for line in commands:
        current_time += 1
        command = Command(line, current_time)
        if ignore_rules.is_match(command.get_unique_command_id()):
            continue
        store.add_command(command)
        output.append(command.get_unique_command_id())
    if mark_read:
        with open(store_file, 'a') as command_filestore:
            for command_str in output:
                command_filestore.write(command_str + '\n')
        with open(history_file_path, "a") as myfile:
            myfile.write(f'{PROCESSED_TO_TAG}\n')


def get_file_path(directory_path: str) -> str:
    """Get the sql db file given the directory where the files is."""
    return os.path.join(directory_path, REMEMBER_DB_FILE_NAME)


def load_command_store(db_file_name: str) -> SqlCommandStore:
    """Get the sql command store from the input file."""
    if not os.path.exists(db_file_name):
        raise Exception(f'db file: {db_file_name} does not exist')
    return SqlCommandStore(db_file_name)


def _init_tables_if_not_exists(db_conn: sqlite3.Connection, table_name: str = TABLE_NAME) -> None:
    """ Create the table if it doesn't exist in the DB."""
    if not check_table_exists(db_conn, table_name):
        create_db_tables(db_conn)


def _create_db_connection(db_file_path: str) -> sqlite3.Connection:
    """Create and return the DB connection."""
    return sqlite3.connect(db_file_path)


def check_table_exists(db_conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if the sql table exists."""
    c = db_conn.cursor()
    c.execute(TABLE_EXISTS_QUERY.format(table_name))
    db_conn.commit()
    if c.fetchone()[0] == 1:
        return True
    return False


def _create_command_search_select_query(search_term: List, starts_with: bool, sort: bool,
                                        search_info: bool) -> str:
    """Create the sql select query for search."""
    where_terms = []
    prepend_term = '' if starts_with else '%'
    for term in search_term:
        like_term = prepend_term + term + '%'
        where_terms.append("full_command LIKE '{}'".format(like_term))
        if search_info:
            where_terms.append("command_info LIKE '{}'".format(like_term))
    where_clause = 'WHERE ' + ' OR '.join(where_terms)
    query = SEARCH_COMMANDS_QUERY.format(where_clause)
    if sort:
        query = query + ' ORDER BY count_seen DESC, last_used DESC'
    return query


def create_db_tables(db_conn: sqlite3.Connection) -> None:
    """ create a database connection to a SQLite database """
    print('Creating table')
    c = db_conn.cursor()
    c.execute(SQL_CREATE_REMEMBER_TABLE)


def save_last_search(file_path: str, last_search_result: List[Command]) -> None:
    with open(file_path, 'w') as file_handler:
        for search_command in last_search_result:
            file_handler.write('%s\n' % search_command.get_unique_command_id())


def read_last_search(file_path: str) -> List[str]:
    with open(file_path) as read_file:
        return [x.strip() for x in read_file.readlines()]
