import snowflake_builder.utilities.string_utilities as string_utilities


def test_strip_first_line():
    assert string_utilities.strip_first_line('abc\ndef\nghi\njkl') == 'def\nghi\njkl'
    assert string_utilities.strip_first_line('a') == ''
    assert string_utilities.strip_first_line('') == ''


def test_strip_last_line():
    assert string_utilities.strip_last_line('abc\ndef\nghi\njkl') == 'abc\ndef\nghi'
    assert string_utilities.strip_last_line('a') == ''
    assert string_utilities.strip_last_line('') == ''


def test_strip_first_and_last_lines():
    assert string_utilities.strip_first_and_last_lines('abc\ndef\nghi\njkl') == 'def\nghi'
    assert string_utilities.strip_first_and_last_lines('a') == ''
    assert string_utilities.strip_first_and_last_lines('') == ''


def test_convert_to_single_line():
    assert string_utilities.convert_to_single_line('abc\ndef\nghi\njkl') == 'abcdefghijkl'
    assert string_utilities.convert_to_single_line('a') == 'a'
    assert string_utilities.convert_to_single_line('') == ''


def test_replace_tags():
    test_string = 'Hello my name is {NAME} and I am from {PLACE}.  Greetings {TO}.'
    values = {
        'NAME': 'Dave',
        'PLACE': 'Earth',
        'TO': 'aliens'
    }
    result = string_utilities.replace_tags(test_string, values)
    assert result == 'Hello my name is Dave and I am from Earth.  Greetings aliens.'


def test_get_text_table():
    headings = ['A', 'B', 'C', 'D']
    row1 = ['Here is', 'a', 'number', '1']
    row2 = ['And here', 'are several', 'more numbers', '2 3 4 5']
    lines = [headings, row1, row2]
    actual_result = string_utilities.get_text_table(lines)
    expected_result = [
        'A         B            C             D        ',
        'Here is   a            number        1        ',
        'And here  are several  more numbers  2 3 4 5  ']
    assert actual_result == expected_result
