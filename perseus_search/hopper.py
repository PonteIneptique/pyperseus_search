""" Really simply python function/class set to use the search interface of Perseus using Python.
Feel free to update, propose setup.py and anything else ;)


"""

import requests
import requests_cache
import bs4
from typing import List, Tuple, Set, Iterator
import re
import urllib.parse

from perseus_search.results import Match

__all__ = [
    "search"
]


_search_results_re = re.compile(r"SearchResults")
_title_re = re.compile(r"More\((\d+)\)")
_space_strip_re = re.compile(r"(\s+)")


def _space_strip(x: str) -> str:
    """ Replace numerous spaces by only one space

    :param x: Input string
    :return: Clean string
    """
    return _space_strip_re.sub(" ", x)


def _get_data(query: str, language: str = "English", page: int = 1) -> str:
    """ Performs a request on Perseus Hopper

    :param query: Word to search for
    :param language: Language to search in
    :param page: Page to retrieve
    :return: String representation of the HTML retrieved
    """
    req = requests.get("http://www.perseus.tufts.edu/hopper/searchresults", params={
        "q": query,
        "inContent": "true",
        "language": language,
        "page": page
    })
    req.raise_for_status()
    return req.text


def _parse(html_content: str) -> bs4.Tag:
    """ Parse the HTML

    :param html_content: String representing the HTML
    :return: Parsed Html
    """
    html = bs4.BeautifulSoup(html_content, features="html.parser")
    return html


def _pagination(html_content: bs4.Tag) -> Iterator[int]:
    """Given an HTML page of Perseus Hopper, returns tuples of bs4 tags which represents the header, the editor
    information and the results

    :param html_content: Parsed HTML from hopper
    :yield: Pages (starting from 2)
    """
    link = html_content.select(".pager a")
    if link:
        uri: urllib.parse.ParseResult = urllib.parse.urlparse(link[-1].attrs["href"])
        page: str = urllib.parse.parse_qs(uri.query).get("page", [""])[-1]
        if page.isnumeric():
            yield from range(2, (int(page)+1))


def _get_results_triple(html_content: bs4.Tag) -> Tuple[bs4.Tag, bs4.Tag, List[bs4.Tag]]:
    """ Given an HTML page of Perseus Hopper, returns tuples of bs4 tags which represents the header, the editor
    information and the results

    :param html_content: Parsed HTML from hopper
    :return: [(title <tr>, editor <tr>, [result <tr>])]
    """
    titles: List[bs4.Tag] = html_content.find_all("tr", class_="trResultTitleBar")
    for title in titles:
        editor = title.find_next("tr", class_="trResultEditorBar")
        results: List[bs4.Tag] = [editor.find_next_sibling("tr", class_=_search_results_re)]

        while results[-1].find_next("tr", class_=_search_results_re):
            if results[-1].find_previous_sibling("tr", class_="trResultTitleBar") != title:
                break
            results.append(results[-1].find_next("tr", class_=_search_results_re))

        yield title, editor, results


def _simplify(tag: bs4.Tag) -> List[Match]:
    """ Simplify the output of a result by removing the "..." tokens and splitting around them

    :param tag: Tag containg the result (a <tr>)
    :return: List of parsed matches
    """
    link = tag.td.a
    if link:
        link = link.extract()
        link = link.attrs.get("href")
    sentences: List[List[str]] = [[]]

    for match in tag.td.children:
        if isinstance(match, bs4.NavigableString):
            clean = _space_strip(str(match).replace(": ...", "")).strip()
            if "..." in clean:
                before, after, *_ = tuple(clean.split("..."))
                sentences[-1].extend(before.split())
                sentences.append(after.split())
            else:
                sentences[-1].extend(clean.split())
        else:
            sentences[-1].append("#"+match.string.strip()+"#")

    return list([
        Match(words, link=link)
        for words in sentences
    ])


def _get_sentences(html: bs4.Tag) -> Set[Match]:
    """ Get sentences from a Perseus Search HTML page

    :param html: HTML parsed from Hopper
    :return: Set of sentences
    """
    sentence_set = set()
    for tag_title, tag_editor, list_results in _get_results_triple(html):
        for tag_result in set(list_results):
            for sentence in _simplify(tag_result):
                sentence_set.add(sentence)
    return sentence_set


def search(query: str, language: str = "English", cache: bool = True) -> Iterator[Match]:
    """ Perform a search on Perseus Hopper in [language] for the string [query] and returns matches in context

    :param query: Search query
    :param language: Language to search in [English, Latin, Greek]
    :param cache: Use requests_cache
    :yields: Matches
    """
    if cache:
        requests_cache.install_cache('ignore.sqlite')
    content: str = _get_data(query, language=language)
    html: bs4.Tag = _parse(content)
    matches: set = _get_sentences(html)

    for page in _pagination(html):
        content = _get_data(query, language=language, page=page)
        html = _parse(content)
        matches.update(_get_sentences(html))

    for match in matches:
        yield match


if __name__ == "__main__":
    for match_index, match in enumerate(search("Amiens", "English")):
        print(match_index, match)

