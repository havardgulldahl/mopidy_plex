# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import string
import unicodedata
from urlparse import parse_qs, urlparse

from mopidy import backend
from mopidy.models import Album, SearchResult, Track

import pafy

import pykka

import requests

from mopidy_plex import logger

def resolve_track(track, stream=False):
    raise NotImplemented
    logger.debug("Resolving YouTube for track '%s'", track)
    if hasattr(track, 'uri'):
        return resolve_url(track.comment, stream)
    else:
        return resolve_url(track.split('.')[-1], stream)


def safe_url(uri):
    raise NotImplemented
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    safe_uri = unicodedata.normalize(
        'NFKD',
        unicode(uri)
    ).encode('ASCII', 'ignore')
    return re.sub(
        '\s+',
        ' ',
        ''.join(c for c in safe_uri if c in valid_chars)
    ).strip()


def resolve_url(url, stream=False):
    raise NotImplemented
    try:
        video = pafy.new(url)
        if not stream:
            uri = '%s/%s.%s' % (
                video_uri_prefix, safe_url(video.title), video.videoid)
        else:
            uri = video.getbestaudio()
            if not uri:  # get video url
                uri = video.getbest()
            logger.debug('%s - %s %s %s' % (
                video.title, uri.bitrate, uri.mediatype, uri.extension))
            uri = uri.url
        if not uri:
            return
    except Exception as e:
        # Video is private or doesn't exist
        logger.info(e.message)
        return

    images = []
    if video.bigthumb is not None:
        images.append(video.bigthumb)
    if video.bigthumbhd is not None:
        images.append(video.bigthumbhd)

    track = Track(
        name=video.title,
        comment=video.videoid,
        length=video.length * 1000,
        album=Album(
            name='YouTube',
            images=images
        ),
        uri=uri
    )
    return track


def search_youtube(q):
    raise NotImplemented
    query = {
        'part': 'id',
        'maxResults': 15,
        'type': 'video',
        'q': q,
        'key': yt_key
    }
    result = session.get(yt_api_endpoint+'search', params=query)
    data = result.json()

    resolve_pool = ThreadPool(processes=16)
    playlist = [item['id']['videoId'] for item in data['items']]

    playlist = resolve_pool.map(resolve_url, playlist)
    resolve_pool.close()
    return [item for item in playlist if item]


def resolve_playlist(url):
    raise NotImplemented
    resolve_pool = ThreadPool(processes=16)
    logger.info("Resolving YouTube-Playlist '%s'", url)
    playlist = []

    page = 'first'
    while page:
        params = {
            'playlistId': url,
            'maxResults': 50,
            'key': yt_key,
            'part': 'contentDetails'
        }
        if page and page != "first":
            logger.debug("Get YouTube-Playlist '%s' page %s", url, page)
            params['pageToken'] = page

        result = session.get(yt_api_endpoint+'playlistItems', params=params)
        data = result.json()
        page = data.get('nextPageToken')

        for item in data["items"]:
            video_id = item['contentDetails']['videoId']
            playlist.append(video_id)

    playlist = resolve_pool.map(resolve_url, playlist)
    resolve_pool.close()
    return [item for item in playlist if item]


class PlexBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(PlexBackend, self).__init__(audio=audio)
        self.config = config
        self.library = PlexLibraryProvider(backend=self)
        self.playback = PlexPlaybackProvider(audio=audio, backend=self)
        self.playlists = None # TODO: Support plex playlists

        self.uri_schemes = ['plex', ]


class PlexLibraryProvider(backend.LibraryProvider):
    def lookup(self, uri):
        '''Lookup the given URIs.
        Return type:    
        list of mopidy.models.Track '''

        if 'plex:' in uri:
            track = uri.replace('plex:', '')

        return [item for item in [self.__resolve(uri)] if item]


    def __resolve(self, uri):
        '''Resolve plex uri to a track'''

    def get_images(self, uris):
        '''Lookup the images for the given URIs

        Backends can use this to return image URIs for any URI they know about be it tracks, albums, playlists... The lookup result is a dictionary mapping the provided URIs to lists of images.

        Unknown URIs or URIs the corresponding backend couldn’t find anything for will simply return an empty list for that URI.

        Parameters: uris (list of string) – list of URIs to find images for
        Return type:    {uri: tuple of mopidy.models.Image}'''


    def search(self, query=None, uris=None, exact=False):
        '''Search the library for tracks where field contains values.

        Parameters: 
        query (dict) – one or more queries to search for
        uris (list of string or None) – zero or more URI roots to limit the search to
        exact (bool) – if the search should use exact matching
        '''

        if not query:
            return

        raise NotImplemented

        if 'uri' in query:
            search_query = ''.join(query['uri'])
            url = urlparse(search_query)
            if 'youtube.com' in url.netloc:
                req = parse_qs(url.query)
                if 'list' in req:
                    return SearchResult(
                        uri=search_uri,
                        tracks=resolve_playlist(req.get('list')[0])
                    )
                else:
                    logger.info(
                        "Resolving YouTube for track '%s'", search_query)
                    return SearchResult(
                        uri=search_uri,
                        tracks=[t for t in [resolve_url(search_query)] if t]
                    )
        else:
            search_query = ' '.join(query.values()[0])
            logger.info("Searching YouTube for query '%s'", search_query)
            return SearchResult(
                uri=search_uri,
                tracks=search_youtube(search_query)
            )


class PlexPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        raise NotImplemented
        track = resolve_track(uri, True)
        if track is not None:
            return track.uri
        else:
            return None
