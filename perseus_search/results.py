import re
from typing import List

__all__ = ["Match"]

_space_format_re = re.compile(r"\s(\W[\s\w])")


def _reput_space(inp: str) -> str:
    """ Put spaces back in a string where it should stay

    :param inp: Input string
    :return: Clean string
    """
    return _space_format_re.sub("\\1 ", inp)


class Match:
    """ Captures information about each match, keeping in memory the search word
    and the link"""

    words: List[str]
    link: str
    match: str

    def __init__(self, words: List[str], link: str):
        self.words: List[str] = words
        self.link: str = link
        self.match: str = ""

        for word_index, word in enumerate(words):
            if word.startswith("#") and word.endswith("#"):
                self.match = word.replace("#", "")
                self.words[word_index] = self.match

    def __str__(self):
        return _reput_space(" ".join(self.words))

    def _format_match(self, w: str) -> str:
        """ Format the match """
        if w == self.match:
            return "<match>"+w+"</match>"
        return w

    def __repr__(self) -> str:
        return _reput_space(" ".join([
            self._format_match(w)
            for w in self.words
        ])).replace("<m atch>", " <match>")  # Because I am lazy to fix the regexp
