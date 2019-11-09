"""
This Module contains the core logic for the remember functions.
"""
import sqlite3
import os.path

from remember.sql_query_constants import SQL_CREATE_REMEMBER_TABLE, SEARCH_COMMANDS_QUERY, \
    SIMPLE_SELECT_COMMAND_QUERY, DELETE_FROM_REMEMBER, GET_ROWID_FOR_COMMAND, \
    INSERT_INTO_REMEMBER_QUERY, UPDATE_COUNT_QUERY, TABLE_EXISTS_QUERY, TABLE_NAME

import re
import shutil
import time

PROCESSED_TO_TAG = '****** previous commands read *******'
FILE_STORE_NAME = 'command_storage.txt'
REMEMBER_DB_FILE_NAME = 'remember.db'
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


def print_commands(commands, highlighted_terms=None):
    """Pretty print the commands."""
    if highlighted_terms is None:
        highlighted_terms = []
    x = 1
    for command in commands:
        print_command(x, command, highlighted_terms)
        x = x + 1
    return ""


def print_command(index, command, highlighted_terms=None):
    """Pretty print a single command."""
    if highlighted_terms is None:
        highlighted_terms = []
    command_str = command.get_unique_command_id()
    info_str = command.get_command_info()
    for term in highlighted_terms:
        command_str = command_str.replace(term, bcolors.OKGREEN + term + bcolors.YELLOW)
        info_str = info_str.replace(term, bcolors.OKGREEN + term + bcolors.YELLOW)
    print(bcolors.HEADER + '(' + str(index) + '): ' + bcolors.YELLOW + command_str
          + bcolors.OKBLUE + " --count:" + str(command.get_count_seen()) + bcolors.ENDC)
    if info_str:
        print(bcolors.FAIL + "Command context/info: " + info_str + bcolors.ENDC)


class IgnoreRules(object):
    """ This class holds the set of ignore rules for commands."""

    def __init__(self):
        self._start_with = []
        self._contains = []
        self._matches = set()

    def is_match(self, command_str):
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

    def add_starts_with(self, command_str):
        """Add a starts with rule to ignore."""
        self._start_with.append(command_str)

    def add_contains(self, command_str):
        """Add a contains with rule to ignore."""
        self._contains.append(command_str)

    def add_matches(self, command_str):
        """Add a exact matches with rule to ignore."""
        self._matches.add(command_str)

    @staticmethod
    def create_ignore_rule(src_file):
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


class Command(object):
    """This class holds the basic pieces for a command."""

    def __init__(self, command_str="", last_used=time.time(), count_seen=1):
        self._command_str = Command.get_currated_command(command_str)
        self._context_before = set()
        self._context_after = set()
        self._manual_comments = "Place any comments here."
        self._parse_command(self._command_str)
        self._count_seen = count_seen
        self._last_used = last_used
        self._command_info = ""

    def _parse_command(self, command):
        """Set the primary command."""
        command_split = command.split(" ")
        if command_split[0] == ".":
            self._primary_command = command_split[1]
            self._command_args = command_split[2:]
        else:
            self._primary_command = command_split[0]
            self._command_args = command_split[1:]

    def get_command_args(self):
        """Get the input args for the command"""
        # This is for backwards compatibility with earlier picked classes that
        # didn't have this field.
        if not hasattr(self, '_command_args'):
            self._parse_command(self.get_unique_command_id())
        return self._command_args

    def get_command_info(self):
        """Get the input args for the command"""
        # This is for backwards compatibility with earlier picked classes that
        # didn't have this field.
        if not hasattr(self, '_command_info'):
            self._command_info = ""
        return self._command_info

    def get_primary_command(self):
        """Get the primary command."""
        return self._primary_command

    def get_unique_command_id(self):
        """Get the commands unique id."""
        return self._command_str

    def get_count_seen(self):
        """Get the count seen."""
        return self._count_seen

    def _increment_count(self):
        """Increment the count of the command."""
        self._count_seen += 1

    def _update_time(self, updated_time):
        """Update the time to this new time."""
        self._last_used = updated_time

    def last_used_time(self):
        """Get the last used time in seconds from epoch"""
        if not hasattr(self, '_last_used'):
            self._last_used = 0
        return self._last_used

    def set_command_info(self, info):
        self._command_info = info

    @classmethod
    def get_currated_command(cls, command_str):
        """Given a command string curate the string and return."""
        currated_command = re.sub(' +', ' ', command_str.strip())
        if currated_command.startswith(":"):
            p = re.compile(";")
            m = p.search(currated_command)
            if m and len(currated_command) > m.start() + 1:
                currated_command = currated_command[m.start() + 1:].strip()
        return currated_command


def _get_unread_commands(src_file):
    """Read the history file and get all the unread commands."""
    unproccessed_lines = []
    tmp_hist_file = src_file + '.tmp'
    shutil.copyfile(src_file, tmp_hist_file)
    try:
        for line in reversed(open(tmp_hist_file, 'rb').readlines()):
            try:
                line = line.decode("utf-8")
            except UnicodeDecodeError as e:
                continue
            if PROCESSED_TO_TAG in line:
                return list(reversed(unproccessed_lines))
            unproccessed_lines.append(line.strip())
    finally:
        os.remove(tmp_hist_file)
    return unproccessed_lines


def read_history_file(
    store,
    src_file,
    store_file,
    ignore_file=None,
    mark_read=True):
    """Read in the history files."""

    commands = _get_unread_commands(src_file)
    output = []
    if ignore_file:
        ignore_rules = IgnoreRules.create_ignore_rule(ignore_file)
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
        with open(src_file, "a") as myfile:
            myfile.write(PROCESSED_TO_TAG + "\n")


def get_file_path(directory_path):
    """Get the pickle file given the directory where the files is."""
    return os.path.join(directory_path, REMEMBER_DB_FILE_NAME)


def _load_command_store_from_sql(db_file_name):
    if not os.path.exists(db_file_name):
        raise Exception(f'db file: {db_file_name} does not exist')
    return SqlCommandStore(db_file_name)


def load_command_store(file_name):
    """Get the command store from the input file."""
    return _load_command_store_from_sql(file_name)


def init_tables_if_not_exists(db_conn):
    if not check_table_exists(db_conn, TABLE_NAME):
        create_db_tables(db_conn)


def create_db_connection(db_file_path):
    db_conn = None
    try:
        db_conn = sqlite3.connect(db_file_path)
        return db_conn
    except sqlite3.Error as e:
        print(e)
    return db_conn


def check_table_exists(db_conn, table_name):
    c = db_conn.cursor()
    c.execute(TABLE_EXISTS_QUERY.format(table_name))
    db_conn.commit()
    if c.fetchone()[0] == 1:
        return True
    return False


class SqlCommandStore(object):
    def __init__(self, db_file=':memory:'):
        self._db_file = db_file
        self._tables_created = None
        self._db_conn = None

    def _get_db_conn(self):
        if not self._db_conn:
            self._db_conn = create_db_connection(self._db_file)
            assert self._db_conn
            if not self._tables_created:
                init_tables_if_not_exists(self._db_conn)
                self._tables_created = True
        return self._db_conn

    def add_command(self, command):
        row_id = self._get_rowid_of_command(command.get_unique_command_id())
        db_conn = self._get_db_conn()
        with db_conn:
            cursor = db_conn.cursor()
            if row_id:
                cursor.execute(UPDATE_COUNT_QUERY, (command.last_used_time(), row_id,))
            else:
                row_insert = (command.get_unique_command_id(), command.get_count_seen(),
                              command.last_used_time(), command.get_command_info())
                cursor.execute(INSERT_INTO_REMEMBER_QUERY, row_insert)

    def _get_rowid_of_command(self, command_str):
        db_conn = self._get_db_conn()
        cursor = db_conn.cursor()
        cursor.execute(GET_ROWID_FOR_COMMAND, (command_str,))
        data = cursor.fetchone()
        if data is None:
            return None
        else:
            return data[0]

    def delete_command(self, command_str):
        db_conn = self._get_db_conn()
        with db_conn:
            cur = db_conn.cursor()
            cur.execute(DELETE_FROM_REMEMBER, (command_str,))
            db_conn.commit()
            if cur.rowcount == 0:
                return None
            return command_str

    def has_command(self, command):
        """This method checks to see if a command is in the store. """
        return self.has_command_by_name(command.get_unique_command_id())

    def has_command_by_name(self, command_str):
        """This method checks to see if a command (by name) is in the store.
        """
        db_conn = self._get_db_conn()
        cursor = db_conn.cursor()
        cursor.execute(SIMPLE_SELECT_COMMAND_QUERY, (command_str,))
        data = cursor.fetchall()
        if len(data) == 0:
            return False
        return True

    def get_num_commands(self):
        """This method returns the number of commands in the store."""
        db_conn = self._get_db_conn()
        cursor = db_conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM {}'.format('remember'))
        count = cursor.fetchall()
        print('\nTotal rows: {}'.format(count[0][0]))
        return count[0][0]

    def search_commands(self,
                        search_terms,
                        starts_with=False,
                        sort=True,
                        search_info=False):
        """This method searches the command store for the command given."""
        search_query = _create_command_search_select_query(search_terms, starts_with, sort,
                                                           search_info)
        matches = []
        db_conn = self._get_db_conn()
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(search_query)
            rows = cursor.fetchall()
            for row in rows:
                command = Command(row[0], row[2], row[1])
                command.set_command_info(row[3])
                matches.append(command)
        return matches

    def close(self):
        if self._db_conn:
            self._db_conn.close()


def _create_command_search_select_query(search_term, starts_with, sort,
                                        search_info):
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


def create_db_tables(db_conn):
    """ create a database connection to a SQLite database """
    print('Creating table')
    try:
        c = db_conn.cursor()
        c.execute(SQL_CREATE_REMEMBER_TABLE)
    except sqlite3.Error as e:
        print(e)
