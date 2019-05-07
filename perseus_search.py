import requests
import requests_cache
import bs4
from typing import List, Tuple, Set
import re
from collections import Counter

requests_cache.install_cache('ignore.sqlite')

_search_results_re = re.compile(r"SearchResults")
_title_re = re.compile(r"More\((\d+)\)")
_space_strip_re = re.compile(r"(\s+)")
_space_format_re = re.compile(r"\s(\W[\s\w])")


def _reput_space(inp: str) -> str:
    return _space_format_re.sub("\\1 ", inp)


class Match:
    def __init__(self, words: List[str], link: str):
        self.words = words
        self.link = link
        self.match = ""
        for word_index, word in enumerate(words):
            if word.startswith("#") and word.endswith("#"):
                self.match = word.replace("#", "")
                self.words[word_index] = self.match

    def __str__(self):
        return _reput_space(" ".join(self.words))

    def format_match(self, w) -> str:
        if w == self.match:
            return "<match>"+w+"</match>"
        return w

    def __repr__(self) -> str:
        return _reput_space(" ".join([
            self.format_match(w)
            for w in self.words
        ]))


def _space_strip(x: str) -> str:
    return _space_strip_re.sub(" ", x)


def _get_data(query: str, language: str="English", page: int=1) -> str:
    req = requests.get("http://www.perseus.tufts.edu/hopper/searchresults", params={
        "q": query,
        "inContent": "true",
        "language": language,
        "page": page
    })
    req.raise_for_status()
    return req.text


def _parse(html_content: str):
    html = bs4.BeautifulSoup(html_content, features="html.parser")
    return html


def _get_results_triple(html_content: bs4.Tag) -> Tuple[bs4.Tag, bs4.Tag, List[bs4.Tag]]:
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
            #print(matcxh.name)
            sentences[-1].append("#"+match.string.strip()+"#")

    return list([
        Match(words, link=link)
        for words in sentences
    ])


def get_sentences(html: bs4.Tag) -> Set[Match]:
    sentence_set = set()
    for tag_title, tag_editor, list_results in _get_results_triple(html):
        for tag_result in set(list_results):
            for sentence in _simplify(tag_result):
                sentence_set.add(sentence)
    return sentence_set


if __name__ == "__main__":
    content = _get_data("Amiens", language="English")
    html = _parse(content)
    matches = list(get_sentences(html))
    for match_index, match in enumerate(matches):
        print(match.link, match)

