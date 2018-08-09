import requests
import spacy
from bs4 import BeautifulSoup

MAIN_WIKI = 'https://en.wikipedia.org/wiki/Lists_of_people_by_nationality'
BASE_WIKI = 'https://en.wikipedia.org'
NLP_MODEL = spacy.load('en_core_web_lg')


def get_pages(demonym_file):
    """Gets individual famous people pages by nationality
    
    Arguments:
        demonym_file {txt} -- path to file containing country demonyms
    
    Returns:
        str[] -- list of urls to individual country pages
    """

    result = requests.get(MAIN_WIKI)
    soup = BeautifulSoup(result.content, 'html.parser')

    demonyms = []
    with open(demonym_file) as fp:
        demonyms = fp.read().splitlines() 

    pages = []
    first_ul = soup.find_all('ul')[1]
    for li_tag in first_ul.find_all('li'):
        if li_tag.text in demonyms:
            pages.append(BASE_WIKI + li_tag.a.attrs['href'])
    return pages


def get_people(pages, output_file):
    """Given a list of pages, gets all people's names
    
    Arguments:
        pages {str[]} -- list of urls to famous people from country pages
        output_file {str} -- path to store output
    """

    people = []
    for page in pages:
        result = requests.get(page)
        soup = BeautifulSoup(result.content, 'html.parser')
        if soup.find('div', {'class': 'navbox'}): 
            soup.find('div', {'class': 'navbox'}).decompose()
        div = soup.find('div', {'id': 'mw-content-text'})
        for li_tag in div.find_all('li'):
            if li_tag.a and li_tag.a.has_attr('title') and li_tag.a.has_attr('href'): 
                doc = NLP_MODEL(li_tag.a.text)
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        people.append(ent.text)
    with open(output_file, 'w') as fp:
        for person in people:
            fp.write(str(person) +"\n")


if __name__== "__main__":
    pages = get_pages('../../common/text_files/country_demonyms.txt')
    get_people(pages, '../../common/text_files/famous_people.txt')