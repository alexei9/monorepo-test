def strip_first_line(s: str) -> str:
    """
    Remove the first line of text from a string containing multiple lines of text.

    Parameters
    ----------
    s : str
        The string to remove the first line of text from.

    Returns
    -------
    str
       The string with the first line of text removed.
    """
    lines = s.splitlines()
    if len(lines) > 0:
        lines.pop(0)
    return '\n'.join(lines)


def strip_last_line(s: str) -> str:
    """
    Remove the last line of text from a string containing multiple lines of text.

    Parameters
    ----------
    s : str
        The string to remove the last line of text from.

    Returns
    -------
    str
       The string with the last line of text removed.
    """
    lines = s.splitlines()
    if len(lines) > 0:
        lines.pop(len(lines)-1)
    return '\n'.join(lines)


def strip_first_and_last_lines(s: str) -> str:
    """
    Remove the first and last lines of text from a string containing multiple lines of text.

    Parameters
    ----------
    s : str
        The string to remove the first and last lines of text from.

    Returns
    -------
    str
       The string with the first and last lines of text removed.
    """
    return strip_first_line(strip_last_line(s))


def convert_to_single_line(s: str) -> str:
    lines = s.splitlines()
    return ''.join(lines)


def replace_tags(s: str, d: dict[str, str]) -> str:
    """
    Replace tags of the format {TAG_NAME} in a string with values specified from a dictionary.

    Parameters
    ----------
    s : str
        The string containing the tags which are to be replaced with values from the dictionary.
    d : dict[str, str]
        The dictionary containing the tag names (as keys) and values.

    Returns
    -------
    str
        The original string with the tags replaced by values from the dictionary.
    """
    wip = s
    for key, value in d.items():
        wip = wip.replace('{' + key + '}', value)
    return wip


def get_text_table(rows: list[list[str]]) -> list[str]:
    """
    Format a collection of strings into tabular format by padding values for presentation purposes.

    Parameters
    ----------
    rows : list[list[str]
        A list representing each row of values, where each row is itself a list of column values.

    Returns
    -------
    list[str]
        A list representing lines of text, where the values in each line are vertically aligned for presentation
        purposes.
    """
    max_column_lengths = []
    for row in rows:
        for c, value in enumerate(row):
            if value is None:
                continue
            value_length = len(value)
            if (c + 1) > len(max_column_lengths):
                max_column_lengths.append(0)
            if value_length > max_column_lengths[c]:
                max_column_lengths[c] = value_length
    lines = []
    for row in rows:
        line = ''
        for c, value in enumerate(row):
            if value is None:
                value = ''
            line = line + value.ljust(max_column_lengths[c] + 2)
        lines.append(line)
    return lines
