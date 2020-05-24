# flake8: noqa
import unittest

from remember.sql_store import _create_command_search_select_query, Command, _rerank_matches, \
    SqlCommandStore


class MyTestCase(unittest.TestCase):
    def test_create_select_query_whenSingleTermAll3_ShouldReturnAll3Query(self) -> None:
        query = _create_command_search_select_query(['grep'], True, True, True)
        expected = "SELECT * FROM remember WHERE full_command LIKE 'grep%' OR " \
                   "command_info LIKE 'grep%' ORDER BY count_seen DESC, last_used DESC"
        self.assertEqual(expected, query)


    def test_create_select_query_whenSingleTermNoSpecial_ShouldReturnBasicQuery(self) -> None:
        query = _create_command_search_select_query(['grep'], False, False, False)
        expected = "SELECT * FROM remember WHERE full_command LIKE '%grep%'"
        self.assertEqual(expected, query)

    def test_create_select_query_whenSingleTermSorted_ShouldReturnBasicSortQuery(self) -> None:
        query = _create_command_search_select_query(['grep'], False, True, False)
        expected = "SELECT * FROM remember WHERE full_command LIKE '%grep%' ORDER BY " \
                   "count_seen DESC, last_used DESC"
        self.assertEqual(expected, query)

    def test_create_select_query_whenSingleTermStartsWith_ShouldReturnStartsWithQuery(self) -> None:
        query = _create_command_search_select_query(['grep'], True, False, False)
        expected = "SELECT * FROM remember WHERE full_command LIKE 'grep%'"
        self.assertEqual(expected, query)

    def test_create_select_query_whenSingleTermStartsWithAndSort_ShouldReturnBothQuery(self) -> None:
        query = _create_command_search_select_query(['grep'], True, True, False)
        expected = "SELECT * FROM remember WHERE full_command LIKE 'grep%' " \
                   "ORDER BY count_seen DESC, last_used DESC"
        self.assertEqual(expected, query)

    def test_rerank_whenMoreTermsInLater_shouldReorderCommands(self) -> None:
        command_str = 'one two three'
        c1 = Command(command_str)
        command_str = 'one match only'
        c2 = Command(command_str)
        command_str = 'one two matches in this'
        c3 = Command(command_str)
        command_str = 'two matches in this one also'
        c4 = Command(command_str)
        matches = [c3, c2, c4,  c1]
        reranked_result = _rerank_matches(matches, ['one', 'two', 'three'])
        expected = [c1, c3, c4, c2]
        self.assertListEqual(expected, reranked_result)

    def test_Command_whenCommandStringIsDot_shouldParseCorrectlyAndNotCrash(self) -> None:
        command_str = '.'
        c1 = Command(command_str)
        c1.get_command_args()

    def test_SqlCommandStore_isEmpty(self) -> None:
        command_store = SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())

    def test_search_commands_whenTermIsDifferentCase_shouldNotReturn(self) -> None:
        store = SqlCommandStore(':memory:')
        store.add_command(Command('Add'))
        matches = store.search_commands(["add"])
        self.assertEqual(0, len(matches))
        matches = store.search_commands(["Add"])
        self.assertEqual(1, len(matches))

    def test_search_commands_whenHasContext_shouldCorrectlyAddContext(self) -> None:
        store = SqlCommandStore(':memory:')
        store.add_command(Command(command_str='Add', directory_context='directory/path'))
        matches = store.search_commands(["Add"])
        self.assertEqual(1, len(matches))

    def test_store_add_whenCommandHasContext_shouldInsertWithContext(self) -> None:
        command_store = SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        context_path = 'some/directory/context'
        command1 = Command(command_str, 10.0, 1, 'command info', context_path)
        command_str2 = "some second command"
        command2 = Command(command_str2, 10.0, 1, 'command info', context_path)
        command_store.add_command(command1)
        command_store.add_command(command2)
        self.assertEqual(2, command_store.get_num_commands())

    def test_get_commands_from_context_whenContextQueried_shouldReturn2Commands(self) -> None:
        command_store = SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        context_path = 'some/directory/context'
        command1 = Command(command_str, 11.0, 1, 'command info 1', context_path)
        command_str2 = "some second command"
        command2 = Command(command_str2, 12.0, 2, 'command info 2', context_path)
        command_store.add_command(command1)
        command_store.add_command(command2)
        results = command_store.get_command_with_context(context_path)
        self.assertEqual(2, command_store.get_num_commands())
        self.assertEqual(2, len(results))
        self.assertEqual(command_str2, results[0].get_unique_command_id())
        self.assertEqual(command_str, results[1].get_unique_command_id())
        self.assertEqual(context_path, results[0].get_directory_context())
        self.assertEqual(context_path, results[1].get_directory_context())

    def test_get_commands_from_context_whenContextQueried_shouldReturn1Commands(self) -> None:
        command_store = SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        context_path = 'some/directory/context'
        context_path2 = 'notqueried/dir'
        command1 = Command(command_str, 11.0, 1, 'command info 1', context_path)
        command_str2 = "some second command"
        command2 = Command(command_str2, 12.0, 2, 'command info 2', context_path2)
        command_store.add_command(command1)
        command_store.add_command(command2)
        results = command_store.get_command_with_context(context_path)
        self.assertEqual(2, command_store.get_num_commands())
        self.assertEqual(1, len(results))
        self.assertEqual(context_path, results[0].get_directory_context())

    def test_add_command_whenSameContextAddedTwice_shouldUpdateTheEntryCount(self) -> None:
        command_store = SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        context_path = 'some/directory/context'
        command1 = Command(command_str, 11.0, 1, 'command info 1', context_path)
        command_store.add_command(command1)
        command_store.add_command(command1)
        results = command_store.get_command_with_context(context_path)
        self.assertEqual(1, command_store.get_num_commands())
        self.assertEqual(1, len(results))
        self.assertEqual(context_path, results[0].get_directory_context())

    def test_add_commands_whenCommandAdded2Time_shouldReflectInCount(self) -> None:
        command_store = SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        context_path = 'some/directory/context'
        context_path2 = 'notqueried/dir'
        command1 = Command(command_str, 11.0, 1, 'command info 1', context_path)
        command_str2 = "some second command"
        command2 = Command(command_str2, 12.0, 2, 'command info 2', context_path2)
        command_store.add_command(command1)
        command_store.add_command(command2)
        results = command_store.get_command_with_context(context_path)
        self.assertEqual(2, command_store.get_num_commands())
        self.assertEqual(1, len(results))
        self.assertEqual(context_path, results[0].get_directory_context())

    def test_search_commands_sorted(self) -> None:
        command_store = SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        command = Command(command_str, 10.0, 1)
        command_store.add_command(command)
        command_str2 = "somelater command string"
        command2 = Command(command_str2, 20.0, 1)
        command_store.add_command(command2)

        result = command_store.search_commands(["some"], starts_with=False, sort=True)
        self.assertEqual(result[0].get_unique_command_id(), command2.get_unique_command_id())
        self.assertEqual(result[1].get_unique_command_id(), command.get_unique_command_id())

    def test_addCommandToSqlStore_whenAddingCommand_shouldBeInStore(self) -> None:
        command_store = SqlCommandStore(':memory:')
        self.assertEqual(0, command_store.get_num_commands())
        command_str = "some command string"
        directory_path = 'directory/path'
        command = Command(command_str, directory_context=directory_path)
        command_store.add_command(command)
        self.assertTrue(command_store.has_command(command))
        self.assertFalse(command_store.has_command(Command("some other command")))
        self.assertEqual(1, command_store.get_num_commands())
        self.assertEqual(1, command_store.get_num_commands())
