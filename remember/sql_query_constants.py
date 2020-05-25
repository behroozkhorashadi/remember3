_REMEMBER = 'remember'
_DIRECTORIES = 'directories'
_COMMAND_CONTEXT = 'command_context'

# Create table statements
SQL_CREATE_REMEMBER_TABLE = \
    f"""
CREATE TABLE IF NOT EXISTS {_REMEMBER}(
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    full_command TEXT UNIQUE ,
    count_seen INTEGER NOT NULL ,
    last_used REAL NOT NULL ,
    command_info TEXT);"""

SQL_CREATE_DIR_TABLE = \
    f"""
CREATE TABLE IF NOT EXISTS {_DIRECTORIES} (
  rowid INTEGER PRIMARY KEY AUTOINCREMENT,
  dir_path TEXT UNIQUE); """

CREATE_CONTEXT_COMMAND_TABLE = \
    f"""
CREATE TABLE IF NOT EXISTS {_COMMAND_CONTEXT} (
  command_id INTEGER NOT NULL,
  context_id INTEGER NOT NULL,
  num_occurrences INTEGER NOT NULL,
  UNIQUE(command_id, context_id),
  FOREIGN KEY(command_id) REFERENCES {_REMEMBER}(rowid) ON DELETE CASCADE,
  FOREIGN KEY(context_id) REFERENCES {_DIRECTORIES}(rowid) ON DELETE CASCADE
);"""

CREATE_TABLES = {_REMEMBER: SQL_CREATE_REMEMBER_TABLE,
                 _DIRECTORIES: SQL_CREATE_DIR_TABLE,
                 _COMMAND_CONTEXT: CREATE_CONTEXT_COMMAND_TABLE}

# Insert statements
INSERT_INTO_REMEMBER_QUERY = f''' INSERT INTO {_REMEMBER}(
                                    full_command,
                                    count_seen,
                                    last_used,
                                    command_info) VALUES(?,?,?,?) '''

INSERT_INTO_DIRECTORIES_QUERY = f'''INSERT INTO {_DIRECTORIES}(dir_path) VALUES(?)'''
INSERT_INTO_COMMAND_CONTEXT = f'INSERT INTO {_COMMAND_CONTEXT} VALUES(?,?,1);'

# Delete statements
DELETE_FROM_REMEMBER = f' DELETE FROM {_REMEMBER} WHERE full_command=?'

# Update statements
UPDATE_REMEMBER_COUNT_QUERY = f'''UPDATE {_REMEMBER}
                                 SET count_seen = count_seen + 1,
                                     last_used = ?
                                 WHERE rowid = ?'''
UPDATE_COMMAND_CONTEXT_COUNT_QUERY = f'''UPDATE {_COMMAND_CONTEXT}
                                     SET num_occurrences = num_occurrences + 1
                                     WHERE rowid = ?;'''

UPDATE_COMMAND_INFO_QUERY = f''' UPDATE {_REMEMBER}
                                 SET command_info = ?
                                 WHERE full_command = ?'''

# Simple select statements
SIMPLE_SELECT_COMMAND_QUERY = f"SELECT rowid FROM {_REMEMBER} WHERE full_command = ?"

GET_ROWID_FROM_DIRECTORIES = f"SELECT rowid FROM {_DIRECTORIES} WHERE dir_path = ?"

GET_ROWID_FROM_COMMAND_CONTEXT = \
    f"""
SELECT rowid
FROM {_COMMAND_CONTEXT}
WHERE command_id = ? AND context_id = ?"""

SEARCH_COMMANDS_QUERY = """
SELECT
    full_command,
    count_seen,
    last_used,
    command_info
FROM """ + _REMEMBER + ' {} '

TABLE_EXISTS_QUERY = ''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}' '''

# Join select statements
SELECT_CONTEXT_COMMANDS = \
    """
    SELECT
      remember.full_command,
      remember.last_used,
      command_context.num_occurrences,
      remember.command_info,
      directories.dir_path as dir_path
    FROM
      directories
    INNER JOIN
      command_context ON directories.rowid = command_context.context_id
    INNER JOIN
      remember ON remember.rowid = command_context.command_id
    WHERE
      directories.dir_path= ? {}
    ORDER BY
      remember.last_used DESC;
    """

PRAGMA_STR = 'PRAGMA case_sensitive_like = true;'
FOREIGN_KEY_PRAGMA = 'PRAGMA foreign_keys = ON;'
