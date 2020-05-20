# flake8: noqa
import unittest

from remember.sql_store import _create_command_search_select_query, Command, _rerank_matches


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
