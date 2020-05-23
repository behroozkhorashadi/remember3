_REMEMBER = 'remember'
_DIRECTORIES = 'directories'
_COMMAND_CONTEXT = 'command_context'

# Create table statements
SQL_CREATE_REMEMBER_TABLE = f""" CREATE TABLE IF NOT EXISTS {_REMEMBER}(
                                    full_command TEXT PRIMARY KEY ,
                                    count_seen INTEGER NOT NULL ,
                                    last_used REAL NOT NULL ,
                                    command_info TEXT);"""

SQL_CREATE_DIR_TABLE = f"""  CREATE TABLE IF NOT EXISTS {_DIRECTORIES} (dir_path TEXT PRIMARY_KEY); """

CREATE_CONTEXT_COMMAND_TABLE = f""" CREATE TABLE IF NOT EXISTS {_COMMAND_CONTEXT} (
                                        command_id INTEGER,
                                        context_id INTEGER,
                                        UNIQUE(command_id, context_id),
                                        FOREIGN KEY(command_id) REFERENCES {_REMEMBER}(rowid),
                                        FOREIGN KEY(context_id) REFERENCES {_DIRECTORIES}(rowid));"""

CREATE_TABLES = {_REMEMBER: SQL_CREATE_REMEMBER_TABLE,
                 _DIRECTORIES: SQL_CREATE_DIR_TABLE,
                 _COMMAND_CONTEXT: CREATE_CONTEXT_COMMAND_TABLE}

# Insert statements
INSERT_INTO_REMEMBER_QUERY = f''' INSERT INTO {_REMEMBER}(
                                    full_command, 
                                    count_seen, 
                                    last_used,
                                    command_info) VALUES(?,?,?,?) '''

INSERT_INTO_DIRECTORIES_QUERY = f'''INSERT INTO {_DIRECTORIES} VALUES(?)'''
INSERT_OR_IGNORE_COMMAND_CONTEXT = f'INSERT OR IGNORE INTO {_COMMAND_CONTEXT} VALUES(?,?);'

# Delete statements
DELETE_FROM_REMEMBER = f' DELETE FROM {_REMEMBER} WHERE full_command=?'

# Update statements
UPDATE_COUNT_QUERY = f''' UPDATE {_REMEMBER}
                         SET count_seen = count_seen + 1,
                             last_used = ?
                         WHERE rowid = ?'''

UPDATE_COUNT_AND_DIR_QUERY = f''' UPDATE {_REMEMBER}
                                     SET count_seen = count_seen + 1,
                                         last_used = ?,
                                         directory_context_id = ?
                                     WHERE rowid = ?'''

UPDATE_COMMAND_INFO_QUERY = f''' UPDATE {_REMEMBER}
                                 SET command_info = ?
                                 WHERE full_command = ?'''

# Select statements
SIMPLE_SELECT_COMMAND_QUERY = f"SELECT rowid FROM {_REMEMBER} WHERE full_command = ?"
GET_ROWID_FROM_DIRECTORIES = f"SELECT rowid FROM {_DIRECTORIES} WHERE dir_path = ?"
SEARCH_COMMANDS_QUERY = 'SELECT * FROM ' + _REMEMBER + ' {}'
TABLE_EXISTS_QUERY = ''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{}' '''

PRAGMA_STR = 'PRAGMA case_sensitive_like = true;'
