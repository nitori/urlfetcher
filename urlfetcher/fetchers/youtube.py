from urllib.parse import urlparse, parse_qs
import re
import requests
from .. import fetcher, utils
from ..secrets import YOUTUBE_API_KEY, YOUTUBE_LIKE_SYMBOL, YOUTUBE_DISLIKE_SYMBOL


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

    apiurl = 'https://www.googleapis.com/youtube/v3/videos'

    if video_id is not None:
        response = requests.get(apiurl, params=dict(
            id=video_id,
            key=YOUTUBE_API_KEY,
            part='snippet,contentDetails,statistics,status'
        ))
        if response.ok:
            data = response.json()
            if 'items' in data and data['items']:
                yield True
            else:
                yield False
                return
        else:
            yield False
            return
    else:
        yield False
        return
    """
{
    "items": [
        {
            "etag": "\"m2yskBQFythfE4irbTIeOgYYfBU/wfGMwi_ohSxnfEMaO6fCz3G45SU\"",
            "kind": "youtube#video",
            "status": {
                "privacyStatus": "public",
                "license": "youtube",
                "uploadStatus": "processed",
                "embeddable": true,
                "publicStatsViewable": true
            },
            "snippet": {
                "liveBroadcastContent": "none",
                "thumbnails": {
                    "high": {
                        "url": "https://i.ytimg.com/vi/m1cMUC0IeB8/hqdefault.jpg",
                        "width": 480,
                        "height": 360
                    },
                    "standard": {
                        "url": "https://i.ytimg.com/vi/m1cMUC0IeB8/sddefault.jpg",
                        "width": 640,
                        "height": 480
                    },
                    "default": {
                        "url": "https://i.ytimg.com/vi/m1cMUC0IeB8/default.jpg",
                        "width": 120,
                        "height": 90
                    },
                    "medium": {
                        "url": "https://i.ytimg.com/vi/m1cMUC0IeB8/mqdefault.jpg",
                        "width": 320,
                        "height": 180
                    }
                },
                "tags": [
                    "interesting",
                    "funny",
                    "comedy",
                    "hilarious",
                    "current events",
                    "politics"
                ],
                "channelTitle": "Sargon of Akkad",
                "title": "The Unquestionable Idea",
                "channelId": "UC-yewGHQbNFpDrGM0diZOLA",
                "description": "We must not allow the regressive left to define Islam as an idea that is above scrutiny.\n\nPrevious video about Richard Dawkins' deplatforming: https://www.youtube.com/watch?v=W1bI7S0LCos\n\nSocial Media\n\nMinds: https://www.minds.com/Sargon_of_Akkad\nFacebook: https://www.facebook.com/sargonofakkad100/\nTwitter: https://twitter.com/Sargon_of_Akkad\nReddit: https://www.reddit.com/r/SargonofAkkad/\n\nCredits and Sources\n\nIntro animation: Undoomed https://www.youtube.com/channel/UCTrecbx23AAYdmFHDkci0aQ\nOutro Music: https://www.youtube.com/watch?v=etDon1LH1vA\n\nSources: https://www.minds.com/blog/view/736947017346981894",
                "publishedAt": "2017-07-26T14:06:28.000Z",
                "localized": {
                    "description": "We must not allow the regressive left to define Islam as an idea that is above scrutiny.\n\nPrevious video about Richard Dawkins' deplatforming: https://www.youtube.com/watch?v=W1bI7S0LCos\n\nSocial Media\n\nMinds: https://www.minds.com/Sargon_of_Akkad\nFacebook: https://www.facebook.com/sargonofakkad100/\nTwitter: https://twitter.com/Sargon_of_Akkad\nReddit: https://www.reddit.com/r/SargonofAkkad/\n\nCredits and Sources\n\nIntro animation: Undoomed https://www.youtube.com/channel/UCTrecbx23AAYdmFHDkci0aQ\nOutro Music: https://www.youtube.com/watch?v=etDon1LH1vA\n\nSources: https://www.minds.com/blog/view/736947017346981894",
                    "title": "The Unquestionable Idea"
                },
                "categoryId": "25"
            },
            "statistics": {
                "dislikeCount": "100",
                "commentCount": "3490",
                "likeCount": "11013",
                "viewCount": "100008",
                "favoriteCount": "0"
            },
            "id": "m1cMUC0IeB8",
            "contentDetails": {
                "caption": "false",
                "definition": "hd",
                "dimension": "2d",
                "licensedContent": true,
                "duration": "PT13M29S",
                "projection": "rectangular"
            }
        }
    ],
    "pageInfo": {
        "resultsPerPage": 1,
        "totalResults": 1
    },
    "etag": "\"m2yskBQFythfE4irbTIeOgYYfBU/Mpy2xjODDHYx_RRiyl_ysGqIprs\"",
    "kind": "youtube#videoListResponse"
}

    """
    def get(d, path):
        current = d
        for p in path.split('.'):
            try:
                current = current[p]
            except KeyError:
                return None
        return current

    item = data['items'][0]
    channel = get(item, 'snippet.channelTitle')
    title = get(item, 'snippet.title')
    duration = get(item, 'contentDetails.duration')
    dislikes = get(item, 'statistics.dislikeCount')
    likes = get(item, 'statistics.likeCount')
    views = get(item, 'statistics.viewCount')

    parts = []

    if channel is not None:
        parts.append(channel)
    if title is not None:
        parts.append(title)

    if duration is not None:
        # PT13M29S
        m = re.match('^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', duration)
        if m is not None:
            hours, minutes, seconds = m.groups()
            if minutes is None:
                minutes = 0
            if seconds is None:
                seconds = 0
            duration_str = '{:02d}:{:02d}'.format(int(minutes), int(seconds))
            if hours is not None:
                duration_str = '{}:{}'.format(hours, duration_str)
            parts.append(duration_str)

    if views is not None:
        parts.append('{} views'.format(views))

    if dislikes is not None and likes is not None:
        bar_length = 10
        dislikes = int(dislikes)
        likes = int(likes)
        total = dislikes + likes
        r = likes / total
        like_str = YOUTUBE_LIKE_SYMBOL * int(round(r * bar_length))
        dislike_str = YOUTUBE_DISLIKE_SYMBOL * (bar_length - len(like_str))
        parts.append('\x0309,09{}\x0304,04{}\x0f'.format(like_str, dislike_str))

    return 'YouTube', parts



