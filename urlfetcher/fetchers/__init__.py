__author__ = 'Nitori'

from .. import fetcher, utils, USER_AGENT

# order matters. first match will be used
from . import danbooru
from . import youtube
from . import html  # text/html
from . import matroska
from . import images
from . import torrent