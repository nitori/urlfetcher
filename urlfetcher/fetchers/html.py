__author__ = 'Nitori'

from urllib.parse import urljoin

import bs4
import requests
from . import fetcher, utils

MAX_SEEK_SIZE = 64 << 10


@fetcher
def fetch(url, head):
    content_type = head.headers['content-type']
    if content_type.startswith('text/html'):
        yield True
    else:
        yield False
        return

    response = requests.get(url, timeout=5)
    soup = bs4.BeautifulSoup(response.text)
    title = soup.title
    if title is not None:
        page_title = ' '.join(title.text.split())
    else:
        page_title = '<no page title found>'

    collect = [page_title]

    """
    full_content_length = 0
    for img_tags in soup.find_all('img'):
        src = img_tags.get('src', None)
        if src is not None:
            img_url = urljoin(url, src)
            head = requests.head(img_url)
            full_content_length += int(head.headers.get('content-length', 0))

    if full_content_length > 0:
        collect.append('estimated size: {}'.format(utils.format_size(full_content_length)))
    """

    return 'Website: ' + (' | '.join(collect))
