from contextlib import closing
import hashlib

import requests
from .. import fetcher, utils

MAX_SEEK_SIZE = 2 << 20  # 2 MiB


@fetcher
def fetch(url, head):
    content_type = head.headers['content-type']
    content_length = head.headers.get('content-length', None)
    if content_length is not None and int(content_length) > MAX_SEEK_SIZE:
        yield False

    if content_type.startswith('application/x-bittorrent'):
        yield True
    else:
        yield False
        return

    with closing(requests.get(url, stream=True)) as stream:
        buf = b''
        for chunk in stream.iter_content(8<<10):
            buf += chunk
            if len(buf) >= MAX_SEEK_SIZE:
                return

    torrent = TorrentFile()
    torrent.parse(buf)

    if torrent.infohash is None:
        return

    collect = []

    torrent.data['info']['pieces'] = None
    del torrent.data['info']['pieces']

    if 'name' in torrent.data['info']:
        collect.append('Name: {}'.format(torrent.data['info']['name']))

    if 'files' in torrent.data['info']:
        collect.append('{} files'.format(len(torrent.data['info']['files'])))
        file_length = 0
        for file in torrent.data['info']['files']:
            file_length += file.get('length', 0)
        if file_length:
            collect.append('Size: {}'.format(utils.format_size(file_length)))

    return '\x02Torrent:\x02 {}'.format(' \x02|\x02 '.join(collect))


class TorrentFile():

    def __init__(self):
        self.data = {}

        self._buf = b''
        self._pos = 0
        self._fdict = {
            'string': self.tstr,
            b'i': self.tint,
            b'l': self.tlist,
            b'd': self.tdict
        }

        self.use_encoding = True
        self.encoding = 'utf-8'
        self._digest_start_pos = 0
        self.infohash = None
        self.eof = False

    def parse(self, data):
        self._buf = data

        try:
            self.data = self.choose()
        except:
            print('\n\nPOSITION: {:X}\n\n'.format(self._pos))
            raise

        self._buf = b''

    def start_digest(self):
        self._digest_start_pos = self._pos

    def stop_digest(self):
        digest = hashlib.sha1(self._buf[self._digest_start_pos:self._pos])
        self.infohash = digest.hexdigest()

    def choose(self):

        if self._buf[self._pos:self._pos+1].isdigit():
            dat = self._fdict['string']()
        else:
            f = self._fdict[self._buf[self._pos:self._pos+1]]
            self._pos += 1
            dat = f()

        return dat

    def tstr(self):
        delimp = self._buf.find(b':', self._pos)
        slen = int(self._buf[self._pos:delimp])

        string = self._buf[delimp+1:slen+delimp+1]
        if self.use_encoding:
            string = string.decode(self.encoding)

        self._pos = delimp+slen+1
        return string

    def tdict(self):
        d = {}

        b = chr(self._buf[self._pos])
        while b != 'e':
            key = self._fdict['string']()
            if key == 'info':
                self.start_digest()

            if key == 'pieces':
                self.use_encoding = False
            value = self.choose()
            if key == 'pieces':
                self.use_encoding = True

            if key == 'info':
                self.stop_digest()

            d[key] = value
            b = chr(self._buf[self._pos])

        self._pos += 1
        return d

    def tlist(self):
        l = []
        b = chr(self._buf[self._pos])
        while b != 'e':
            l.append(self.choose())
            b = chr(self._buf[self._pos])

        self._pos += 1
        return l

    def tint(self):
        i = ''

        b = chr(self._buf[self._pos])
        while b != 'e':
            i += b
            self._pos += 1
            b = chr(self._buf[self._pos])

        self._pos += 1
        return int(i)
