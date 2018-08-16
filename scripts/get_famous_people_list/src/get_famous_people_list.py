import gzip
from typing import List

import grequests
import progressbar as pb
import requests
import spacy
from bs4 import BeautifulSoup

MAIN_WIKI = 'https://en.wikipedia.org/wiki/Lists_of_people_by_nationality'
BASE_WIKI = 'https://en.wikipedia.org'
NLP_MODEL = spacy.load('en_core_web_lg')


def get_pages(demonym_file: str) -> List[str]:
    """Gets individual famous people pages by nationality

    Arguments:
        demonym_file {txt} -- path to file containing country demonyms

    Returns:
        str[] -- list of urls to individual country pages
    """

    result = requests.get(MAIN_WIKI)
    soup = BeautifulSoup(result.content, 'html.parser')

    demonyms = set()
    with open(demonym_file, encoding='utf-8') as fp:
        demonyms = {entity.strip() for entity in fp}

    pages = set()
    first_ul = soup.find_all('ul')[1]
    for li_tag in first_ul.find_all('li'):
        if li_tag.text in demonyms:
            pages.add(BASE_WIKI + li_tag.a.attrs['href'])
    return list(pages)


def get_people(pages: List[str], output_file: str):
    """Given a list of pages, gets all people's names

    Arguments:
        pages {str[]} -- list of urls to famous people from country pages
        output_file {str} -- path to store output
    """
    widget = ['Fetching list of people: ', pb.Percentage(), ' ',
              pb.Bar(marker=pb.RotatingMarker()), ' ', pb.ETA()]
    timer = pb.ProgressBar(widgets=widget,
                           maxval=len(pages)).start()

    calls = (grequests.get(page) for page in pages)
    responses = grequests.map(calls)
    with gzip.open(output_file, 'wb') as fp:
        for count, result in enumerate(responses):
            soup = BeautifulSoup(result.content, 'html.parser')
            if soup.find('div', {'class': 'navbox'}):
                soup.find('div', {'class': 'navbox'}).decompose()
            div = soup.find('div', {'id': 'mw-content-text'})
            for li_tag in div.find_all('li'):
                if li_tag.a and li_tag.a.has_attr('title') and li_tag.a.has_attr('href'):
                    doc = NLP_MODEL(li_tag.a.text)
                    for ent in doc.ents:
                        if ent.label_ == "PERSON":
                            line = str(ent.text) + "\n"
                            fp.write(line.encode(encoding='utf-8'))
            timer.update(count)            
    timer.finish()


if __name__ == "__main__":
    pages = get_pages('../../common/text_files/country_demonyms.txt')
    get_people(pages, '../../common/text_files/famous_people.txt.gz')
