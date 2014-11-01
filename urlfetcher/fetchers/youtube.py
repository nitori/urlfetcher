__author__ = 'Nitori'

from urllib.parse import urlparse, parse_qs
import requests
from . import fetcher, utils


YOUTUBE_API_URI = 'http://gdata.youtube.com/feeds/api/videos/{video_id}?alt=json'


@fetcher(urlpattern=r'https?://(www\.)?(youtube\.com|youtu\.be)(/.*)?$')
def fetch(url, head):
    urlp = urlparse(url)

    # https://youtu.be/<videoid>
    # https://www.youtube.com/embed/<videoid>
    # https://www.youtube.com/watch?v=<videoid>

    video_id = None
    if urlp.netloc == 'youtu.be':
        video_id = urlp.path[1:]
    else:
        if urlp.path.startswith('/embed/'):
            video_id = urlp.path[7:]
        elif urlp.path.startswith('/watch'):
            qs = parse_qs(urlp.query)
            video_ids = qs.get('v', None)
            if video_ids:
                video_id = video_ids.pop(0)

    response = None
    if video_id is not None:
        api_url = YOUTUBE_API_URI.format(video_id=video_id)
        response = requests.get(api_url)
        if response.ok:
            yield True
        else:
            yield False
            return
    else:
        yield False
        return

    data = response.json()

    entry = data.get('entry', {})

    title = entry.get('title', {}).get('$t', '')
    title = ' '.join(title.split())

    authors = entry.get('author', [])
    author = ''
    if authors:
        author = authors[0].get('name', {}).get('$t', '')
        author = ' '.join(author.split())

    rating = entry.get('gd$rating', {}).get('average', None)
    viewcount = entry.get('yt$statistics', {}).get('viewCount', None)
    duration = entry.get('media$group', {}).get('yt$duration', {}).get('seconds', None)

    collect = []

    if title:
        collect.append(title)

    if author:
        collect.append('by ' + author)

    if duration:
        duration = int(duration)
        collect.append('duration: {}'.format(utils.format_duration(duration)))

    if viewcount:
        collect.append('{} views'.format(int(viewcount)))

    if rating:
        collect.append('rating: {:.1f}'.format(float(rating)))

    return '\x02YouTube:\x02 ' + (' | '.join(collect))



