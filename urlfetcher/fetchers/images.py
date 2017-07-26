from contextlib import closing
import io

# requires Pillow
from PIL import Image
import requests
from .. import fetcher, utils

MAX_SEEK_SIZE = 64 << 10


@fetcher
def fetch(url, head):
    content_type = head.headers['content-type']
    content_length = head.headers.get('content-length', None)
    if content_type.startswith('image/'):
        yield True
    else:
        yield False
        return

    with closing(requests.get(url, stream=True)) as stream:
        buf = b''
        for chunk in stream.iter_content(8<<10):
            buf += chunk
            if len(buf) >= MAX_SEEK_SIZE:
                break

    fp = io.BytesIO(buf)
    im = Image.open(fp)

    width, height = im.size
    img_format = im.format

    mimetype = {
        'png': 'image/png',
        'gif': 'image/gif',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'svg': 'image/svg',
    }

    collect = []
    collect.append('{}x{}'.format(width, height))
    collect.append(mimetype.get(img_format.lower(), img_format.lower()))

    if content_length is not None:
        collect.append('size: {}'.format(utils.format_size(int(content_length))))

    return 'Image: ' + (' | '.join(collect))

