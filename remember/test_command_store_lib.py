# flake8: noqa

import os
import unittest

import remember.command_store_lib as command_store_lib

TEST_PATH_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_FILES_PATH = os.path.join(TEST_PATH_DIR, "test_files")


class TestCommandStoreLib(unittest.TestCase):

    def test_SqlCommandStore_isEmpty(self) -> None:
        command_store = command_store_lib.SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())

    def test_search_commands_with_sqlstore(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        store = command_store_lib.SqlCommandStore(':memory:')
        command_store_lib.read_history_file(store, file_name, "doesntmatter", None, False)
        matches = store.search_commands(["add"], search_info=True)
        self.assertIsNotNone(matches)
        matches = store.search_commands(["add"], True)
        self.assertTrue(len(matches) == 0)
        matches = store.search_commands(["subl"], True)
        self.assertTrue(len(matches) == 1)
        store.close()

    def test_search_commands_sorted(self) -> None:
        command_store = command_store_lib.SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        command = command_store_lib.Command(command_str, 10.0, 1)
        command_store.add_command(command)
        command_str2 = "somelater command string"
        command2 = command_store_lib.Command(command_str2, 20.0, 1)
        command_store.add_command(command2)

        result = command_store.search_commands(["some"], starts_with=False, sort=True)
        self.assertEqual(result[0].get_unique_command_id(), command2.get_unique_command_id())
        self.assertEqual(result[1].get_unique_command_id(), command.get_unique_command_id())

    def test_addCommandToSqlStore(self) -> None:
        command_store = command_store_lib.SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        command = command_store_lib.Command(command_str)
        command_store.add_command(command)
        self.assertTrue(command_store.has_command(command))
        self.assertFalse(command_store.has_command(command_store_lib.Command("some other command")))
        self.assertEqual(1, command_store.get_num_commands())

    def test_getPrimaryCommand_CheckcorrectlyIdPrimaryCommand(self) -> None:
        command_str = "some command string"
        command = command_store_lib.Command(command_str)
        self.assertEqual("some", command.get_primary_command())
        command_str = "  some command string"
        command = command_store_lib.Command(command_str)
        self.assertEqual("some", command.get_primary_command())
        command_str = " . some command string"
        command = command_store_lib.Command(command_str)
        self.assertEqual("some", command.get_primary_command())

    def test_Command_checkConstructor(self) -> None:
        command = command_store_lib.Command(" git branch")
        self.assertEqual("git branch", command.get_unique_command_id())
        command = command_store_lib.Command("git branch")
        self.assertEqual("git branch", command.get_unique_command_id())

    def test_readFile(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        store = command_store_lib.SqlCommandStore(':memory:')
        command_store_lib.read_history_file(store, file_name, "doesntmatter", None, False)
        self.assertTrue(store.has_command_by_name("vim somefile.txt"))
        self.assertTrue(store.has_command_by_name("rm somefile.txt"))
        self.assertTrue(store.has_command_by_name("whereis script"))
        self.assertTrue(store.has_command_by_name("vim /usr/bin/script"))
        self.assertFalse(store.has_command_by_name("vim somefil"))

    def test_readFile_withIgnoreFile(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        ignore_file = os.path.join(TEST_FILES_PATH, "test_ignore_rule.txt")
        store = command_store_lib.SqlCommandStore(':memory:')
        command_store_lib.read_history_file(store, file_name, "doesntmatter", ignore_file, False)
        self.assertFalse(store.has_command_by_name("vim somefile.txt"))
        self.assertTrue(store.has_command_by_name("rm somefile.txt"))
        self.assertTrue(store.has_command_by_name("whereis script"))
        self.assertFalse(store.has_command_by_name("vim /usr/bin/script"))
        self.assertFalse(store.has_command_by_name("vim somefil"))

    def test_verifySqldb_shouldSaveAndStore_whenCommandIsAdded(self) -> None:
        file_name = ''
        try:
            file_name = os.path.join(TEST_PATH_DIR, "delete_test_pickle.db")
            command_store = command_store_lib.SqlCommandStore(file_name)
            command_str = "git branch"
            command = command_store_lib.Command(command_str)
            command_store.add_command(command)
            command_store = command_store_lib.load_command_store(file_name)
            self.assertTrue(command_store.has_command(command))
        finally:
            if file_name:
                os.remove(file_name)

    def test_sqlCommandStore_whenAddingItem_shouldReturnTrueWhenSearching(self) -> None:
        file_path = ''
        try:
            file_path = os.path.join(TEST_PATH_DIR, "delete_test_sql_store.db")
            command_store = command_store_lib.SqlCommandStore(file_path)
            command_str = "git branch"
            command = command_store_lib.Command(command_str)
            command_store.add_command(command)
            command_store = command_store_lib.load_command_store(file_path)
            self.assertTrue(command_store.has_command(command))
        finally:
            if file_path:
                os.remove(file_path)

    def test_verify_read_sql_file(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "remember.db")
        store = command_store_lib.load_command_store(file_name)
        matches = store.search_commands([""], False)
        self.assertTrue(len(matches) > 0)
        matches = store.search_commands(["rm"], True)
        self.assertTrue(len(matches) == 1)
        self.assertEqual(matches[0].get_unique_command_id(), 'rm somefile.txt')
        self.assertEqual(matches[0].get_count_seen(), 2)

    def test_verify_read_sql_file_time(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "remember.db")
        self.assertTrue(os.path.isfile(file_name))
        store = command_store_lib.load_command_store(file_name)
        matches = store.search_commands([""], False)
        for m in matches:
            self.assertEqual(0, m.last_used_time())

    def test_readUnprocessedLinesOnly(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_processed.txt")
        unread_commands = command_store_lib._get_unread_commands(file_name)
        self.assertEqual("vim somefile.txt", unread_commands[0])
        self.assertEqual("git commit -a -m \"renamed directory.\"", unread_commands[1])
        self.assertEqual(2, len(unread_commands))

    def test_CuratedCommands_ReturnCorrectResults(self) -> None:
        self.assertEqual("git foo",
                         command_store_lib.Command.get_currated_command("    git     foo"))
        self.assertEqual(". git foo",
                         command_store_lib.Command.get_currated_command(" .   git     foo"))

    def test_CuratedZshCommands_ReturnRemovedHeaders(self) -> None:
        self.assertEqual("setopt SHARE_HISTORY", command_store_lib.Command.get_currated_command(
            ": 1503848943:0;setopt SHARE_HISTORY"))
        self.assertEqual("echo $HISTFILE; other command",
                         command_store_lib.Command.get_currated_command(
                             ": 1503848500:0;echo $HISTFILE; other command"))

    def test_CurratedZshCommandsWeirdFormat_ReturnRemovedHeaders(self) -> None:
        self.assertEqual("setopt SHARE_HISTORY", command_store_lib.Command.get_currated_command(
            ": 1503848943:0; setopt SHARE_HISTORY"))
        self.assertEqual(": 1503848500:0;", command_store_lib.Command.get_currated_command(
            ": 1503848500:0; "))

    def test_delete_sql_whenExists_shouldDeleteFromStore(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        self.assertTrue(os.path.isfile(file_name))
        store = command_store_lib.SqlCommandStore(':memory:')
        command_store_lib.read_history_file(store, file_name, "doesntmatter", None, False)
        self.assertTrue(store.has_command_by_name("vim somefile.txt"))
        self.assertIsNotNone(store.delete_command('vim somefile.txt'))
        self.assertFalse(store.has_command_by_name("vim somefile.txt"))

    def test_delete_whenDoesntExists_shouldReturnNone(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        self.assertIsNone(store.delete_command('anything'))

    def test_ignoreRule_whenCreate_shouldCreateWorkingIgnoreRule(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_ignore_rule.txt")
        ignore_rule = command_store_lib.create_ignore_rule(file_name)
        self.assertTrue(ignore_rule.is_match(''))
        self.assertTrue(ignore_rule.is_match('vim opensomefile'))
        self.assertFalse(ignore_rule.is_match('svim opensomefile'))
        self.assertTrue(ignore_rule.is_match('vim foo'))
        self.assertFalse(ignore_rule.is_match('svim foos'))
        self.assertTrue(ignore_rule.is_match('git commit -a -m'))
        self.assertFalse(ignore_rule.is_match('git comit -a -m'))
        self.assertFalse(ignore_rule.is_match('git foos'))

    def test_ignoreRule_whenFileDoestExist_shouldNotCrash(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        store = command_store_lib.SqlCommandStore(':memory:')
        command_store_lib.read_history_file(store, file_name, "doesntmatter",
                                            "test_files/fileNotthere.txt", False)

    def test_command_parseArgs(self) -> None:
        command_str = 'git diff HEAD^ src/b/FragmentOnlyDetector.java'
        command = command_store_lib.Command(command_str, 1234.1234)
        self.assertEqual(command.get_primary_command(), 'git')
        self.assertEqual(command.get_command_args(),
                         ['diff', 'HEAD^', 'src/b/FragmentOnlyDetector.java'])
        self.assertEqual(1234.1234, command.last_used_time())
        command_str = 'git'
        command = command_store_lib.Command(command_str, 1234.1234)
        self.assertEqual(command.get_primary_command(), 'git')
        self.assertEqual(command.get_command_args(), [])
        self.assertEqual(1234.1234, command.last_used_time())
        command._increment_count()
        self.assertEqual(1234.1234, command.last_used_time())
        command._update_time(4321)
        self.assertEqual(4321, command.last_used_time())

    def test_get_file_path(self) -> None:
        result = command_store_lib.get_file_path('my_dir/path')
        self.assertEqual('my_dir/path/' + command_store_lib.REMEMBER_DB_FILE_NAME, result)

    def test_load_file_when_file_not_there(self) -> None:
        with self.assertRaises(Exception):
            command_store_lib.load_command_store('randomNonExistantFile.someextension')

    def test_create_select_query_whenSingleTermNoSpecial_ShouldReturnBasicQuery(self) -> None:
        query = command_store_lib._create_command_search_select_query(['grep'], False, False, False)
        expected = "SELECT * FROM remember WHERE full_command LIKE '%grep%'"
        self.assertEqual(expected, query)

    def test_create_select_query_whenSingleTermSorted_ShouldReturnBasicSortQuery(self) -> None:
        query = command_store_lib._create_command_search_select_query(['grep'], False, True, False)
        expected = "SELECT * FROM remember WHERE full_command LIKE '%grep%' ORDER BY " \
                   "count_seen DESC, last_used DESC"
        self.assertEqual(expected, query)

    def test_create_select_query_whenSingleTermStartsWith_ShouldReturnStartsWithQuery(self) -> None:
        query = command_store_lib._create_command_search_select_query(['grep'], True, False, False)
        expected = "SELECT * FROM remember WHERE full_command LIKE 'grep%'"
        self.assertEqual(expected, query)

    def test_create_select_query_whenSingleTermStartsWithAndSort_ShouldReturnBothQuery(self) -> None:
        query = command_store_lib._create_command_search_select_query(['grep'], True, True, False)
        expected = "SELECT * FROM remember WHERE full_command LIKE 'grep%' " \
                   "ORDER BY count_seen DESC, last_used DESC"
        self.assertEqual(expected, query)

    def test_create_select_query_whenSingleTermAll3_ShouldReturnAll3Query(self) -> None:
        query = command_store_lib._create_command_search_select_query(['grep'], True, True, True)
        expected = "SELECT * FROM remember WHERE full_command LIKE 'grep%' OR " \
                   "command_info LIKE 'grep%' ORDER BY count_seen DESC, last_used DESC"
        self.assertEqual(expected, query)


if __name__ == '__main__':
    unittest.main()
