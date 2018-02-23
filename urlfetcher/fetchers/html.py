import bs4
import requests
import chardet
from .. import fetcher, utils, USER_AGENT, TIMEOUT

MAX_SEEK_SIZE = 64 << 10


@fetcher
def fetch(url, head):
    content_type = head.headers['content-type']
    if content_type.startswith('text/html'):
        yield True
    else:
        yield False
        return

    response = requests.get(
        url,
        timeout=TIMEOUT,
        headers={'User-Agent': USER_AGENT})
    if 'charset' not in content_type.lower():
        detected = chardet.detect(response.content)
        text = response.content.decode(detected.get('encoding', 'utf-8'), 'replace')
    else:
        text = response.text
    soup = bs4.BeautifulSoup(text)
    title = soup.title
    if title is not None:
        page_title = ' '.join(title.text.split())
    else:
        page_title = '<no page title found>'

    collect = [page_title]

    return 'Website', collect
