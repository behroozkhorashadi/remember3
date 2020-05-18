import sqlite3
import time
import re
from typing import List, Set, Optional

from remember.sql_query_constants import SQL_CREATE_REMEMBER_TABLE, SEARCH_COMMANDS_QUERY, \
    SIMPLE_SELECT_COMMAND_QUERY, DELETE_FROM_REMEMBER, GET_ROWID_FOR_COMMAND, \
    INSERT_INTO_REMEMBER_QUERY, UPDATE_COUNT_QUERY, TABLE_EXISTS_QUERY, TABLE_NAME, PRAGMA_STR, \
    UPDATE_COMMAND_INFO_QUERY


class Command(object):
    """This class holds the basic pieces for a command."""

    def __init__(self, command_str: str = "", last_used: float = time.time(),
                 count_seen: int = 1, command_info: str = ''):
        self._command_str = Command.get_curated_command(command_str)
        self._context_before: Set = set()
        self._context_after: Set = set()
        self._manual_comments = "Place any comments here."
        self._parse_command(self._command_str)
        self._count_seen = count_seen
        self._last_used = last_used
        self._command_info = command_info

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

    def delete_command(self, command_str: str) -> Optional[str]:
        db_conn = self._get_initialized_db_connection()
        with db_conn:
            cur = db_conn.cursor()
            cur.execute(DELETE_FROM_REMEMBER, (command_str,))
            db_conn.commit()
            if cur.rowcount == 0:
                return None
            return command_str

    def update_command_info(self, command: Command) -> None:
        db_connection = self._get_initialized_db_connection()
        with db_connection:
            cursor = db_connection.cursor()
            cursor.execute(UPDATE_COMMAND_INFO_QUERY,
                           (command.get_command_info(), command.get_unique_command_id(),))

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
                        search_info: bool = False) -> List[Command]:
        """This method searches the command store for the command given."""
        search_query = _create_command_search_select_query(
            search_terms, starts_with, sort, search_info)
        matches = []
        db_conn = self._get_initialized_db_connection()
        with db_conn:
            cursor = db_conn.cursor()
            cursor.execute(search_query)
            rows = cursor.fetchall()
            for row in rows:
                command = Command(row[0], row[2], row[1], row[3])
                matches.append(command)
        return _rerank_matches(matches, search_terms)

    def close(self) -> None:
        if self._db_conn:
            self._db_conn.close()

    def _get_rowid_of_command(self, command_str: str) -> Optional[int]:
        cursor = self._get_initialized_db_connection().cursor()
        cursor.execute(GET_ROWID_FOR_COMMAND, (command_str,))
        data = cursor.fetchone()
        if data is None:
            return None
        else:
            return data[0]

    def _get_initialized_db_connection(self) -> sqlite3.Connection:
        if not self._db_conn:
            self._db_conn = _create_db_connection(self._db_file)
            assert self._db_conn
            self._db_conn.execute(PRAGMA_STR)
            if not self._table_creation_verified:
                _init_tables_if_not_exists(self._db_conn)
                self._table_creation_verified = True
        return self._db_conn


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


def _rerank_matches(commands: List[Command], terms: List[str]) -> List[Command]:
    results: List[List[Command]] = [[] for _ in range(len(terms))]
    for command in commands:
        index = _num_terms_matched_in_command(command, terms) - 1
        results[index].append(command)
    results.reverse()
    reranked_commands = []
    for command_list in results:
        reranked_commands.extend(command_list)
    return reranked_commands


def _num_terms_matched_in_command(command: Command, terms: List[str]) -> int:
    command_str = command.get_unique_command_id()
    count = 0
    for term in terms:
        if term in command_str:
            count += 1
    return count


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


def _init_tables_if_not_exists(db_conn: sqlite3.Connection, table_name: str = TABLE_NAME) -> None:
    """ Create the table if it doesn't exist in the DB."""
    if not _check_table_exists(db_conn, table_name):
        _create_db_tables(db_conn)


def _create_db_connection(db_file_path: str) -> sqlite3.Connection:
    """Create and return the DB connection."""
    return sqlite3.connect(db_file_path)


def _check_table_exists(db_conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if the sql table exists."""
    c = db_conn.cursor()
    c.execute(TABLE_EXISTS_QUERY.format(table_name))
    db_conn.commit()
    if c.fetchone()[0] == 1:
        return True
    return False


def _create_db_tables(db_conn: sqlite3.Connection) -> None:
    """ create a database connection to a SQLite database """
    print('Creating table')
    c = db_conn.cursor()
    c.execute(SQL_CREATE_REMEMBER_TABLE)
