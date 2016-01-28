# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import string
import unicodedata
from urlparse import parse_qs, urlparse

from mopidy import backend, httpclient
from mopidy.models import Album, SearchResult, Track

import pykka

from plexapi.server import PlexServer
from plexapi import audio
from plexapi.library import MusicSection

import requests

from mopidy_plex import logger

def get_requests_session(proxy_config, user_agent):
    proxy = httpclient.format_proxy(proxy_config)
    full_user_agent = httpclient.format_user_agent(user_agent)

    session = requests.Session()
    session.proxies.update({'http': proxy, 'https': proxy})
    session.headers.update({'user-agent': full_user_agent})

    return session




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

        self.plex = PlexServer(config['server'])
        self.music = [s for s in self.plex.library.sections() if s.TYPE==MusicSection.TYPE][0]
        self.session = get_requests_session(
                  proxy_config=config['proxy'],
                  user_agent='%s/%s' % (
                      mopidy_plex.Extension.dist_name,
                      mopidy_plex.__version__))

    def resolve_uri(self, uri_path):
        'Get a leaf uri and complete it'
        return self.plex.url(uri_path)


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
        elem = self.backend.server.query(uri)[0]
        plextrack = plexaudio.build_item(self.backend.server, elem, uri)
        return Track(uri=plextrack.key,
                     name=plextrack.title,
                     artists=[Artist(uri=self.resolve_uri(plextrack.grandparentKey),
                                     name=plextrack.grandparentTitle)],
                     album=Album(uri=self.resolve_uri(plextrack.parentKey),
                                 name=plextrack.parentTitle),
                     track_no=plextrack.index,
                     length=plextrack.duration,
                     # TODO: bitrate=searchhit.media.bitrate,
                     comment=plextrack.summary
                    )

    def get_images(self, uris):
        '''Lookup the images for the given URIs

        Backends can use this to return image URIs for any URI they know about be it tracks, albums, playlists... The lookup result is a dictionary mapping the provided URIs to lists of images.

        Unknown URIs or URIs the corresponding backend couldn’t find anything for will simply return an empty list for that URI.

        Parameters: uris (list of string) – list of URIs to find images for
        Return type:    {uri: tuple of mopidy.models.Image}'''
        return None

    def search(self, query=None, uris=None, exact=False):
        '''Search the library for tracks where field contains values.

        Parameters:
        query (dict) – one or more queries to search for
        uris (list of string or None) – zero or more URI roots to limit the search to
        exact (bool) – if the search should use exact matching

        Returns mopidy.models.SearchResult, which has these properties
            uri (string) – search result URI
            tracks (list of Track elements) – matching tracks
            artists (list of Artist elements) – matching artists
            albums (list of Album elements) – matching albums
        '''

        logger.info("Searching Plex for track '%s'", query)
        if not query:
            return


        if 'uri' in query: # TODO add uri limiting

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
                    return SearchResult(
                        uri=search_uri,
                        tracks=[t for t in [resolve_url(search_query)] if t]
                    )
        else:
            search_query = ' '.join(query.values()[0])

        logger.info("Searching Plex with query '%s'", search_query)


        def wrap_artist(searchhit):
            '''Wrap a plex search result in mopidy.model.artist'''
            return Artist(uri=searchhit.key,
                          name=searchhit.title)

        def wrap_album(searchhit):
            '''Wrap a plex search result in mopidy.model.album'''
            return Album(uri=searchhit.key,
                         name=searchhit.title,
                         artists=[Artist(uri=self.resolve_uri(searchhit.parentKey),
                                         name=searchhit.parentTitle)],
                         num_tracks=searchhit.leafCount,
                         num_discs=None,
                         date=searchhit.year,
                         images=[self.resolve_uri(searchhit.thumb),
                                 self.resolve_uri(searchhit.art)]
                         )

        def wrap_track(searchhit):
            '''Wrap a plex search result in mopidy.model.track'''
            return Track(uri=searchhit.key,
                         name=searchhit.title,
                         artists=[Artist(uri=self.resolve_uri(searchhit.grandparentKey),
                                         name=searchhit.grandparentTitle)],
                         album=Album(uri=self.resolve_uri(searchhit.parentKey),
                                      name=searchhit.parentTitle),
                         track_no=searchhit.index,
                         length=searchhit.duration,
                         # TODO: bitrate=searchhit.media.bitrate,
                         comment=searchhit.summary
                         )


        artists, tracks, albums = []
        for hit in self.backend.music.search(search_query):
            if isinstance(hit, plexaudio.Artist): artists.append(hit)
            elif isinstance(hit, plexaudio.Track): tracks.append(hit)
            elif isinstance(hit, plexaudio.Album): albums.append(hit)

        return SearchResult(
            uri=search_uri,
            tracks=tracks,
            artists=artists,
            albums=albums
        )


class PlexPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        '''Convert custom URI scheme to real playable URI.

        MAY be reimplemented by subclass.

        This is very likely the only thing you need to override as a backend author. Typically this is where you convert any Mopidy specific URI to a real URI and then return it. If you can’t convert the URI just return None.

        Parameters:	uri (string) – the URI to translate
        Return type:	string or None if the URI could not be translated'''

        logger.info("Playback.translate_uri Plex with uri '%s'", uri)

        elem = self.backend.server.query(uri)[0]
        return plexaudio.build_item(self.backend.server, elem, uri).getStreamUrl()


    def _get_time_position(self):
        '''Get the current time position in milliseconds.

        MAY be reimplemented by subclass.

        Return type:	int'''
        raise NotImplemented


    def _pause(self):
        '''Pause playback.

        MAY be reimplemented by subclass.

        Return type:	True if successful, else False'''
        raise NotImplemented

    def _play(self):
        '''Start playback.

        MAY be reimplemented by subclass.

        Return type:	True if successful, else False'''
        raise NotImplemented

    def _resume(self):
        '''Resume playback at the same time position playback was paused.

        MAY be reimplemented by subclass.

        Return type:	True if successful, else False'''
        raise NotImplemented

    def _seek(self, time_position):
        '''Seek to a given time position.

        MAY be reimplemented by subclass.

        Parameters:	time_position (int) – time position in milliseconds
        Return type:	True if successful, else False'''
        raise NotImplemented

    def _stop(self):
        '''Stop playback.

        MAY be reimplemented by subclass.

        Should not be used for tracking if tracks have been played or when we are done playing them.

        Return type:	True if successful, else False'''
        raise NotImplemented
