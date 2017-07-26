from functools import partial

import re
import requests
from types import GeneratorType
import bs4
try:
    import lxml
    bs4.BeautifulSoup = partial(bs4.BeautifulSoup, features='lxml')
except ImportError:
    bs4.BeautifulSoup = partial(bs4.BeautifulSoup, features='html.parser')

__version__ = (1, 1)
USER_AGENT = 'Shanghai/{} by LarryPete'.format(
    '.'.join(str(v) for v in __version__))
TIMEOUT = 3


class Fetcher:
    CATCH = 1

    _fetcher_registry = []

    def __call__(self, func=None, *, urlpattern=None):
        if func is None:
            return partial(self, urlpattern=urlpattern)

        if isinstance(urlpattern, str):
            urlpattern = re.compile(urlpattern)
        self._fetcher_registry.append((urlpattern, func))
        return func

    @classmethod
    def fetch(cls, url):
        response = requests.head(url, headers={'User-Agent': USER_AGENT},
                                 allow_redirects=True, timeout=TIMEOUT)
        redirected_to = None
        if response.history:
            redirected_to = response.url
        for urlpattern, func in cls._fetcher_registry:
            gen = None
            if urlpattern is None:
                gen = func(url, response)
            else:
                if urlpattern.match(url) is not None:
                    gen = func(url, response)

            if gen is not None:
                if not isinstance(gen, GeneratorType):
                    raise TypeError('Expected type {} not {}'.format(
                        GeneratorType, type(gen)))

                cont = next(gen)
                if cont:
                    result = None
                    try:
                        next(gen)
                    except StopIteration as return_result:
                        result = return_result.value
                    if not isinstance(result, str):
                        raise TypeError('Expected type {} not {}'.format(
                            str, type(result)))

                    if redirected_to is not None:
                        if len(redirected_to) <= 150:
                            result = '{} | \x02Redirect\x02: {}'\
                                .format(result, redirected_to)
                        else:
                            result = '{} | \x02Redirect\x02 (URL to long)'\
                                .format(result)
                    return result


fetcher = Fetcher()

from . import fetchers
