import chardet
import requests
from .. import fetcher, utils, USER_AGENT, TIMEOUT

MAX_SEEK_SIZE = 64 << 10


@fetcher
def fetch(url, head):
    content_type = head.headers['content-type']
    if content_type.startswith('text/'):
        yield True
    else:
        yield False
        return

    parts = [content_type]

    content_length = head.headers.get('content-length', None)
    if content_length is not None:
        parts.append(utils.format_size(int(content_length)))

    return 'Textfile', parts
