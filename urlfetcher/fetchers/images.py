from contextlib import closing
from urllib.parse import urljoin
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

    base_url = urljoin(url, '/')
    headers = {
        'Referer': base_url,
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
    }

    collect = []
    response = requests.get(url, stream=True, headers=headers)
    if response.status_code // 100 == 2:
        with closing(response) as stream:
            buf = b''
            for chunk in stream.iter_content(8 << 10):
                buf += chunk
                if len(buf) >= MAX_SEEK_SIZE:
                    break
        fp = io.BytesIO(buf)

        try:
            im = Image.open(fp)
        except OSError:
            if buf.startswith(b'GIF87a') or buf.startswith(b'GIF89a'):
                collect.append('image/gif')
            elif buf.startswith(b'\xFF\xD8'):
                collect.append('image/jpeg')
            elif buf.startswith(b'\x89PNG\r\n\x1a\n'):
                collect.append('image/png')
            elif buf.lstrip().lower().startswith(b'<svg'):
                collect.append('image/svg')
            elif buf.lstrip().lower().startswith((b'<?xml', b'<!')):
                if b'<svg' in buf.lower():
                    collect.append('image/svg')
            else:
                collect.append('Unknown format')
        else:
            get_image_data(collect, im)

        if content_length is not None:
            collect.append('size: {}'.format(utils.format_size(int(content_length))))
    else:
        # non 2xx status code
        collect.append('Received status code {}'.format(response.status_code))

    vision = test_google_vision(url)
    if isinstance(vision, tuple) and len(vision) == 2:
        tags, nsfw = vision
        if nsfw:
            collect.append(', '.join(nsfw))
        if tags:
            collect.append(', '.join(tags))

    return 'Image', collect


def get_image_data(collect, im: Image):
    width, height = im.size
    img_format = im.format

    mimetype = {
        'png': 'image/png',
        'gif': 'image/gif',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'svg': 'image/svg',
    }

    collect.append('{}x{}'.format(width, height))
    collect.append(mimetype.get(img_format.lower(), img_format.lower()))


def test_google_vision(image_url):
    data = {
        'requests': [{
            'image': {
                'source': {'imageUri': image_url},
            },
            'features': [
                {'type': 'LABEL_DETECTION', 'maxResults': VISION_MAXRESULTS},
                {'type': 'SAFE_SEARCH_DETECTION'},
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
        nsfw = []
        trigger_nsfw = ('possible', 'likely', 'very_likely', 'unknown')

        for response in data['responses']:
            for annotation in response['labelAnnotations']:
                tags.append(annotation['description'])

            # Unknown, Very Unlikely, Unlikely, Possible, Likely, and Very Likely
            safe_search = response.get('safeSearchAnnotation', {})

            # "safeSearchAnnotation": {
            #     "adult": "UNLIKELY",
            #     "spoof": "VERY_UNLIKELY",
            #     "medical": "VERY_UNLIKELY",
            #     "violence": "VERY_UNLIKELY"
            # },

            for key in safe_search:
                value = safe_search[key].lower()
                if value in trigger_nsfw:
                    value = value.replace('_', ' ')
                    nsfw.append('\002{}:\002 {}'.format(key.title(), value.title()))

        return tags, nsfw
    return 'Error: Unsupported response type: {}'.format(r.status_code)
