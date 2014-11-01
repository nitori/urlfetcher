__author__ = 'Nitori'

from contextlib import closing
import traceback
import hashlib
import struct
import sys
import io

import enzyme
import requests

from . import fetcher, utils


class HTTPBytesReader:
    CHUNK_SIZE = 64 << 10

    def __init__(self, url, content_length):
        self._content_length = content_length
        self._url = url
        self._bufs = {}
        self._pos = 0
        self.read(self.CHUNK_SIZE)
        self.seek(0)

    def tell(self):
        return self._pos

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self._pos = offset
        elif whence == io.SEEK_CUR:
            self._pos += offset
        elif whence == io.SEEK_END:
            if self._content_length is None:
                raise io.UnsupportedOperation('no Content-Length provided.')
            self._pos = self._content_length - offset
        else:
            raise io.UnsupportedOperation('Unsupported seek operation.')
        return self._pos

    def read(self, size):
        assert size > 0

        if self._pos >= self._content_length:
            return b''

        chunks = size//self.CHUNK_SIZE
        if size % self.CHUNK_SIZE > 0:
            chunks += 1

        base_offset = self._pos - (self._pos % self.CHUNK_SIZE)
        if base_offset not in self._bufs:
            self._read_chunks(base_offset, chunks)

        return_buf = b''
        for chunk in range(chunks):
            buf = self._bufs.get(base_offset+(base_offset*chunk), b'')
            read_from_pos = self._pos - base_offset
            read_to_pos = min(size + read_from_pos, self.CHUNK_SIZE - read_from_pos)
            return_buf += buf[read_from_pos:read_to_pos]
            size -= len(return_buf)

        self._pos += len(return_buf)
        return return_buf

    def _read_chunks(self, offset, chunks):
        bytes_range = 'bytes={}-{}'.format(offset, (offset+(self.CHUNK_SIZE*chunks))-1)
        r = requests.get(self._url, headers={
            'Range': bytes_range
        })
        for chunk in range(chunks):
            self._bufs[offset+(chunk*self.CHUNK_SIZE)] = r.content[:self.CHUNK_SIZE]
        self._print_buf_size()

    def _print_buf_size(self):
        size = 0
        for val in self._bufs.values():
            size += len(val)


@fetcher
def fetch(url, head):
    content_type = head.headers['content-type']
    content_length = head.headers.get('content-length', None)
    if content_length is not None:
        content_length = int(content_length)
    if head.headers.get('accept-ranges', None) != 'bytes':
        yield False
        return

    if content_type.startswith(('video/webm', 'application/octet-stream')):
        reader = HTTPBytesReader(url, content_length)

        buf = reader.read(4)
        reader.seek(0)

        if reader.read(4) == b'\x1a\x45\xdf\xa3':
            yield True
        else:
            yield False
            return
    else:
        yield False
        return

    reader.seek(0)
    mkv = enzyme.MKV(reader)

    collect = []

    if mkv.info.title is not None:
        collect.append('Title: {}'.format(mkv.info.title))

    if content_length is not None:
        collect.append('Size: {}'.format(utils.format_size(content_length)))
    else:
        collect.append('Unknown file size')

    if mkv.info.duration is not None:
        collect.append('Duration: {}'.format(
            utils.format_duration(mkv.info.duration.seconds)))

    if mkv.video_tracks:
        if len(mkv.video_tracks) > 1:
            collect.append('{} video streams'.format(len(mkv.video_tracks)))
        for video in mkv.video_tracks:
            tocollect = []
            if video.codec_id is not None:
                tocollect.append(video.codec_id)
            tocollect.append('{}x{}'.format(video.width, video.height))
            collect.append('Video: {}'.format(' - '.join(tocollect)))

    if mkv.audio_tracks:
        if len(mkv.audio_tracks) > 1:
            collect.append('{} audio streams'.format(len(mkv.audio_tracks)))
        for audio in mkv.audio_tracks:
            tocollect = []
            if audio.codec_id is not None:
                tocollect.append(audio.codec_id)
            if audio.channels is not None:
                tocollect.append('{} channels'.format(audio.channels))
            if audio.language is not None and audio.language != 'und':
                tocollect.append('language: {}'.format(audio.language))
            collect.append('Audio: {}'.format(' - '.join(tocollect)))

    return '\x02Video:\x02 {}'.format(' \x02|\x02 '.join(collect))
