from contextlib import closing
import io

# requires Pillow
from PIL import Image
import requests
from .. import fetcher, utils
from ..secrets import VISION_APIKEY, VISION_REFERER, VISION_MAXRESULTS

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

    collect = [
        '{}x{}'.format(width, height),
        mimetype.get(img_format.lower(), img_format.lower()),
    ]

    if content_length is not None:
        collect.append('size: {}'.format(utils.format_size(int(content_length))))

    vision = test_google_vision(url)
    if vision:
        collect.append(vision)

    return 'Image', collect


def test_google_vision(image_url):
    data = {
        'requests': [{
            'image': {
                'source': {'imageUri': image_url},
            },
            'features': [
                {'type': 'LABEL_DETECTION', 'maxResults': VISION_MAXRESULTS},
            ],
        }]
    }

    r = requests.post(
        'https://vision.googleapis.com/v1/images:annotate',
        json=data,
        params={'key': VISION_APIKEY},
        headers={'Referer': VISION_REFERER}
    )
    if r.status_code == 200:
        data = r.json()
        if len(data['responses']) == 1:
            if 'error' in data['responses'][0]:
                return 'Error: {}'.format(data['responses'][0]['error']['message'])

        tags = []
        for response in data['responses']:
            for annotation in response['labelAnnotations']:
                tags.append(annotation['description'])
        return ', '.join(tags)
    return 'Error: Unsupported response type: {}'.format(r.status_code)
