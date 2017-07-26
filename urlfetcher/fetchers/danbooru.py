from urllib.parse import urlsplit, urlunsplit, urljoin

import requests

from .. import fetcher

# you might need to create this, if you want to access
# non-public data.
try:
    from ..secrets import DANBOORU_LOGIN, DANBOORU_API_KEY
except ImportError:
    DANBOORU_LOGIN = None
    DANBOORU_API_KEY = None

WARNING_TAGS = (
    'yuri', 'yaoi', 'loli', 'shota', 'futanari', 'futa',
    'tentacles', 'guro', 'nude',
    'naked_apron', 'naked_shirt', 'naked_towel',
    'naked_ribbon', 'naked_sheet', 'naked_sweater',
)


@fetcher(urlpattern=r'https?://danbooru\.donmai\.us(/.*)?$')
def fetch(url, head):
    """Danbooru API is accessible by simply appending ".json"
    to the path of the URL.
    """
    urlp = urlsplit(url)
    # modify path and ignore fragment
    newurlp = urlp[0:2] + (urlp.path + '.json',) + urlp[3:4] + ('',)

    api_url = urlunsplit(newurlp)

    if DANBOORU_LOGIN is not None and DANBOORU_API_KEY is not None:
        response = requests.get(api_url, auth=(DANBOORU_LOGIN, DANBOORU_API_KEY))
    else:
        response = requests.get(api_url)
    if response.ok:
        yield True
    else:
        yield False
        return

    data = response.json()
    # import json
    # print(json.dumps(data, indent=4))

    general_tags = data.get('tag_string_general', '').split()
    copyrights = data.get('tag_string_copyright', '').split()
    characters = data.get('tag_string_character', '').split()
    artists = data.get('tag_string_artist', '').split()

    width = int(data.get('image_width', 0))
    height = int(data.get('image_height', 0))

    rating = data.get('rating')

    score = data.get('score', None)
    # down_score = data.get('down_score', None)
    # up_score = data.get('up_score', None)

    file_url = data.get('file_url', None)

    # a list of strings, that will be joined together
    collect = []

    if width and height:
        collect.append('{}x{}'.format(width, height))

    tags_collect = []
    characters_line = tag_joiner(characters)
    if characters_line:
        tags_collect.append(characters_line.strip())

    copyrights_line = tag_joiner(copyrights)
    if copyrights_line:
        if characters_line:
            copyrights_line = '(' + copyrights_line + ')'
        tags_collect.append(copyrights_line.strip())

    artist_line = tag_joiner(artists)
    if artist_line:
        if characters_line or copyrights_line:
            artist_line = '\x02by\x02 ' + artist_line
        tags_collect.append(artist_line.strip())

    if tags_collect:
        collect.append(' '.join(tags_collect))

    if score is not None:
        score = int(score)
        collect.append('Score: {}'.format(score))

    if rating != 's':
        collect.append('Rating: {}'.format(
            'explicit (\x02NSFW\x02)' if rating == 'e' else 'questionable (\x02possibly NSFW\x02)'))

    warn_for = []
    for tag in WARNING_TAGS:
        if tag in general_tags:
            warn_for.append(tag)

    if warn_for:
        collect.append('Warning: {}'.format(
            ', '.join('\x0304\x02{}\x0F'.format(tag) for tag in warn_for)))

    # if file_url is not None:
    #     collect.append(urljoin(url, file_url))

    return '\x02danbooru:\x02 ' + (' | '.join(collect))


def tag_joiner(intags):
    line = ''
    tags = intags[:]
    while tags and len(line) < 50:
        tag = tags.pop(0)
        if not line:
            line = tag
        else:
            line += ', ' + tag
    if tags:
        line += ' (and {} more)'.format(len(tags))
    return line.strip()
