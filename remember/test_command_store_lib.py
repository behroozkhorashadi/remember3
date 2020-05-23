# flake8: noqa
import io
import os
import unittest
from unittest import mock

from mock import patch, mock_open, Mock

import remember.command_store_lib as command_store_lib
from remember.sql_store import SqlCommandStore

TEST_PATH_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_FILES_PATH = os.path.join(TEST_PATH_DIR, "test_files")


class TestCommandStoreLib(unittest.TestCase):
    def test_readHistoryFile_whenFileRead_shouldFinishWithWriteEnd(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        with open(file_name, 'rb') as hist_file:
            hist_file_content = hist_file.read()
        store = SqlCommandStore(':memory:')
        history_processor = command_store_lib.HistoryProcessor(store, file_name, '', 1)
        with patch('remember.command_store_lib.open', mock_open(read_data=hist_file_content)) as m:
            history_processor.process_history_file()
            history_processor.update_history_file()
        handle = m()
        handle.write.assert_called_with(f'{command_store_lib.PROCESSED_TO_TAG}\n')
        matches = store.search_commands(["add"], search_info=True)
        self.assertIsNotNone(matches)
        matches = store.search_commands(["add"], True)
        self.assertTrue(len(matches) == 0)
        matches = store.search_commands(["subl"], True)
        self.assertTrue(len(matches) == 1)

    def test_readHistoryFile_whenDecodeError_shouldReturnOnly1(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        hist_file_content = b"\x81\nOnly Command\n"
        with patch('remember.command_store_lib.open', mock_open(read_data=hist_file_content)):
            lines = command_store_lib.get_string_file_lines(file_name)
            result = command_store_lib.get_unread_commands(
                lines, command_store_lib.HistoryFileType.STANDARD)
        self.assertEqual('Only Command', result[0].command_line())
        self.assertIsNone(result[0].directory_context())

    def test_search_commands_with_sqlstore(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        store = SqlCommandStore(':memory:')
        history_processor = command_store_lib.HistoryProcessor(store, file_name, '', 1)
        history_processor.process_history_file()
        matches = store.search_commands(["add"], search_info=True)
        self.assertIsNotNone(matches)
        matches = store.search_commands(["add"], True)
        self.assertTrue(len(matches) == 0)
        matches = store.search_commands(["subl"], True)
        self.assertTrue(len(matches) == 1)

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
        history_processor = command_store_lib.HistoryProcessor(store, file_name, '', 1)
        history_processor.process_history_file()
        self.assertTrue(store.has_command_by_name("vim somefile.txt"))
        self.assertTrue(store.has_command_by_name("rm somefile.txt"))
        self.assertTrue(store.has_command_by_name("whereis script"))
        self.assertTrue(store.has_command_by_name("vim /usr/bin/script"))
        self.assertFalse(store.has_command_by_name("vim somefil"))

    def test_readFile_withIgnoreFile(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        store = command_store_lib.SqlCommandStore(':memory:')
        history_processor = command_store_lib.HistoryProcessor(store, file_name, TEST_FILES_PATH, 1)
        history_processor.process_history_file()
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
        file_name = os.path.join(TEST_FILES_PATH, "test_remember.db")
        store = command_store_lib.load_command_store(file_name)
        matches = store.search_commands([""], False)
        self.assertTrue(len(matches) > 0)
        matches = store.search_commands(["rm"], True)
        self.assertTrue(len(matches) == 1)
        self.assertEqual(matches[0].get_unique_command_id(), 'rm somefile.txt')
        self.assertEqual(matches[0].get_count_seen(), 2)

    def test_verify_read_sql_file_time(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_remember.db")
        self.assertTrue(os.path.isfile(file_name))
        store = command_store_lib.load_command_store(file_name)
        matches = store.search_commands([""], False)
        for m in matches:
            self.assertEqual(0, m.last_used_time())

    def test_readUnprocessedLinesOnly(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_2unprocessed.txt")
        lines = command_store_lib.get_string_file_lines(file_name)
        unread_commands = command_store_lib.get_unread_commands(
            lines, command_store_lib.HistoryFileType.STANDARD)
        self.assertEqual("vim somefile.txt", unread_commands[0].command_line())
        self.assertEqual("git commit -a -m \"renamed directory.\"",
                         unread_commands[1].command_line())
        self.assertEqual(2, len(unread_commands))

    def test_get_unread_commands_custom_file_when1SimpleCommand_shouldParseAndSplitCorrectly(self) -> None:
        unread_commands = command_store_lib._get_unread_commands_custom_file(
            ['/github/remember3<<!>>: 1589958292:0;vim somefile.txt'])
        self.assertEqual(": 1589958292:0;vim somefile.txt", unread_commands[0].command_line())
        self.assertEqual("/github/remember3", unread_commands[0].directory_context())
        self.assertEqual(1, len(unread_commands))

    def test_get_unread_commands_whenOnly3Commands_shouldAlsoGetContext(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "custom_history_file.txt")
        file_lines = open(file_name).readlines()
        unread_commands = command_store_lib.get_unread_commands(
            file_lines, command_store_lib.HistoryFileType.CUSTOM)
        self.assertEqual(": 1589958292:0;vim somefile.txt", unread_commands[0].command_line())
        self.assertEqual("/github/remember3", unread_commands[0].directory_context())
        self.assertEqual(": 1589958318:0;git commit -a -m \"renamed directory.\"",
                         unread_commands[1].command_line())
        self.assertEqual("/github/remember3",
                         unread_commands[1].directory_context())
        self.assertEqual(": 1589958318:0; some othercommand", unread_commands[2].command_line())
        self.assertEqual("/Behrooz/code/", unread_commands[2].directory_context())
        self.assertEqual(3, len(unread_commands))

    def test_CuratedCommands_ReturnCorrectResults(self) -> None:
        self.assertEqual("git foo",
                         command_store_lib.Command.get_curated_command("    git     foo"))
        self.assertEqual(". git foo",
                         command_store_lib.Command.get_curated_command(" .   git     foo"))

    def test_CuratedZshCommands_ReturnRemovedHeaders(self) -> None:
        self.assertEqual("setopt SHARE_HISTORY", command_store_lib.Command.get_curated_command(
            ": 1503848943:0;setopt SHARE_HISTORY"))
        self.assertEqual("echo $HISTFILE; other command",
                         command_store_lib.Command.get_curated_command(
                             ": 1503848500:0;echo $HISTFILE; other command"))

    def test_CurratedZshCommandsWeirdFormat_ReturnRemovedHeaders(self) -> None:
        self.assertEqual("setopt SHARE_HISTORY", command_store_lib.Command.get_curated_command(
            ": 1503848943:0; setopt SHARE_HISTORY"))
        self.assertEqual(": 1503848500:0;", command_store_lib.Command.get_curated_command(
            ": 1503848500:0; "))

    def test_delete_sql_whenExists_shouldDeleteFromStore(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        self.assertTrue(os.path.isfile(file_name))
        store = command_store_lib.SqlCommandStore(':memory:')
        history_processor = command_store_lib.HistoryProcessor(store, file_name, '', 1)
        history_processor.process_history_file()
        self.assertTrue(store.has_command_by_name("vim somefile.txt"))
        self.assertIsNotNone(store.delete_command('vim somefile.txt'))
        self.assertFalse(store.has_command_by_name("vim somefile.txt"))

    def test_delete_whenDoesntExists_shouldReturnNone(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        self.assertIsNone(store.delete_command('anything'))

    def test_ignoreRule_whenCreate_shouldCreateWorkingIgnoreRule(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "ignore_rules.txt")
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
        store = command_store_lib.SqlCommandStore()
        processor = command_store_lib.HistoryProcessor(store, file_name, 'not there')
        processor.process_history_file()

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

    def test_get_file_path(self) -> None:
        result = command_store_lib.get_file_path('my_dir/path')
        self.assertEqual('my_dir/path/' + command_store_lib.REMEMBER_DB_FILE_NAME, result)

    def test_load_file_when_file_not_there(self) -> None:
        with self.assertRaises(Exception):
            command_store_lib.load_command_store('randomNonExistantFile.someextension')

    def test_print_commands_whenSingleCommand_shouldPrint(self) -> None:
        command_str = 'git diff HEAD^ src/b/FragmentOnlyDetector.java'
        command = command_store_lib.Command(command_str, 1234.1234)
        command_list = [command]
        with patch('sys.stdout', new_callable=io.StringIO) as std_out_mock:
            command_store_lib.print_commands(command_list)
            expected = command_store_lib._create_indexed_highlighted_print_string(
                1, command_str, command) + '\n'
            self.assertEqual(expected, std_out_mock.getvalue())

    def test_print_commands_whenSingleCommandWithHighlights_shouldPrintWithHighlights(self) -> None:
        command_str = 'git diff'
        command = command_store_lib.Command(command_str, 1234.1234)
        command_list = [command]
        with patch('sys.stdout', new_callable=io.StringIO) as std_out_mock:
            command_store_lib.print_commands(command_list, ['git'])
            expected = command_store_lib._create_indexed_highlighted_print_string(
                1, command_str, command) + '\n'
            expected = command_store_lib._highlight_term_in_string(expected, 'git')
            self.assertEqual(expected, std_out_mock.getvalue())

    def test_update_command_whenAddCommandToStore_shouldSetBackingStore(self) -> None:
        store = command_store_lib.SqlCommandStore()
        command = command_store_lib.Command('Some command')
        store.add_command(command)
        command_info_str = 'Some Info'
        command.set_command_info(command_info_str)
        store.update_command_info(command)
        result = store.search_commands(['Some'])[0]
        self.assertEqual(command.get_unique_command_id(), result.get_unique_command_id())
        self.assertEqual(command_info_str, result.get_command_info())

    @mock.patch('remember.command_store_lib.HistoryProcessor.update_history_file')
    def test_when_generate_from_args_should_call_into_command_store_lib(
            self, mock_read_file: Mock) -> None:
        history_file_path = 'some/path'
        return_result_list = ['1', '2']
        store = command_store_lib.SqlCommandStore()
        with patch('remember.command_store_lib.get_string_file_lines', return_value=return_result_list):
            with patch('remember.command_store_lib.load_command_store', return_value=store) :
                command_store_lib.generate_store_from_args(history_file_path, TEST_FILES_PATH)
                mock_read_file.assert_called_once_with()

    def test_start_history_processing_when_process_history_file_shouldCorrectlyAddToStore(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_input.txt")
        with open(file_name, 'rb') as hist_file:
            hist_file_content = hist_file.read()
        store = command_store_lib.SqlCommandStore(':memory:')

        with patch('remember.command_store_lib.open', mock_open(read_data=hist_file_content)) as m:
            command_store_lib.start_history_processing(store, file_name, 'doesntmatter', 10)
        handle = m()
        handle.write.assert_called_with(f'{command_store_lib.PROCESSED_TO_TAG}\n')
        matches = store.search_commands(["add"], search_info=True)
        self.assertIsNotNone(matches)
        matches = store.search_commands(["add"], True)
        self.assertTrue(len(matches) == 0)
        matches = store.search_commands(["subl"], True)
        self.assertTrue(len(matches) == 1)

    def test_HistoryProcessor_when_process_history_fileOnProcessedFile_shouldNotRun(self) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "test_processed.txt")
        with open(file_name, 'rb') as hist_file:
            hist_file_content = hist_file.read()
        store = command_store_lib.SqlCommandStore(':memory:')
        with patch('remember.command_store_lib.open', mock_open(read_data=hist_file_content)) as m:
            command_store_lib.start_history_processing(store, file_name, 'doesntmatter', 10)
        handle = m()
        handle.write.assert_not_called()
