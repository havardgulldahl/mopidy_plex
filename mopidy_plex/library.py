# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import urllib

from mopidy import backend
from mopidy.models import Artist, Album, SearchResult, Track, Ref

from plexapi import audio as plexaudio

from mopidy_plex import logger


class PlexLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri='plex:directory', name='Plex Music')


    def __init__(self, *args, **kwargs):
        super(PlexLibraryProvider, self).__init__(*args, **kwargs)
        self.plex = self.backend.plex
        self._root = []
        self._root.append(Ref.directory(uri='plex:album', name='Albums'))
        self._root.append(Ref.directory(uri='plex:artist', name='Artists'))

    def _item_ref(self, item, item_type):
        if item_type == 'track':
            _ref = Ref.track
        else:
            _ref = Ref.directory
        return _ref(uri=self.plex.plex_uri(item.ratingKey, 'plex:{}'.format(item_type)),
                    name=item.title)

    def browse(self, uri):
        logger.debug('browse: %s', str(uri))
        if not uri:
            return []
        if uri == self.root_directory.uri:
            return self._root
        parts = uri.split(':')

        # albums
        if uri == 'plex:album':
            logger.debug('self._browse_albums()')
            return [self._item_ref(item, 'album') for item in
                    plexaudio.list_items(self.plex, '/library/sections/4/albums')]

        # a single album
        # uri == 'plex:album:album_id'
        if len(parts) == 3 and parts[1] == 'album':
            logger.debug('self._browse_album(uri)')
            album_id = parts[2]
            return [self._item_ref(item, 'track') for item in
                    plexaudio.list_items(self.plex,
                                         '/library/metadata/{}/children'.format(album_id))]

        # artists
        if uri == 'plex:artist':
            logger.debug('self._browse_artists()')
            return [self._item_ref(item, 'artist') for item in
                    plexaudio.list_items(self.plex, '/library/sections/4/all')]

        # a single artist
        # uri == 'plex:artist:artist_id'
        if len(parts) == 3 and parts[1] == 'artist':
            logger.debug('self._browse_artist(uri)')
            artist_id = parts[2]
            # get albums and tracks
            ret = []
            for item in plexaudio.list_items(self.plex,
                                             '/library/metadata/{}/children'.format(artist_id)):
                ret.append(self._item_ref(item, 'album'))
            for item in plexaudio.list_items(self.plex,
                                             '/library/metadata/{}/allLeaves'.format(artist_id)):
                ret.append(self._item_ref(item, 'track'))
            return ret

        # all tracks of a single artist
        # uri == 'plex:artist:artist_id:all'
        if len(parts) == 4 and parts[1] == 'artist' and parts[3] == 'all':
            logger.debug('self._browse_artist_all_tracks(uri)')
            artist_id = parts[2]
            return [self._item_ref(item, 'track') for item in
                    plexaudio.list_items(self.plex, '/library/metadata/{}/allLeaves'.format(artist_id))]

        logger.debug('Unknown uri for browse request: %s', uri)

        return []

    def lookup(self, uri):
        '''Lookup the given URIs.
        Return type:
        list of mopidy.models.Track '''

        logger.info("Lookup Plex uri '%s'", uri)

        parts = uri.split(':')

        if uri.startswith('plex:artist:'):
            # get all tracks for artist
            item_id = parts[2]
            plex_uri = '/library/metadata/{}/allLeaves'.format(item_id)
        elif uri.startswith('plex:album:'):
            # get all tracks for album
            item_id = parts[2]
            plex_uri = '/library/metadata/{}/children'.format(item_id)
        elif uri.startswith('plex:track:'):
            # get track
            item_id = parts[2]
            plex_uri = '/library/metadata/{}'.format(item_id)

        ret = []
        for item in self.plex.query(plex_uri):
            plextrack = plexaudio.build_item(self.plex,
                                             item,
                                             '/library/metadata/{}'.format(item.attrib['ratingKey']))
            ret.append(wrap_track(plextrack, self.backend.plex_uri))
        return ret


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
        query (dict) – one or more queries to search for - the dict's keys being:
              {
                  'any': *, # this is what we get without explicit modifiers
                  'albumartist': *,
                  'date': *,
                  'track_name': *,
                  'track_number': *,
              }


        uris (list of string or None) – zero or more URI roots to limit the search to
        exact (bool) – if the search should use exact matching

        Returns mopidy.models.SearchResult, which has these properties
            uri (string) – search result URI
            tracks (list of Track elements) – matching tracks
            artists (list of Artist elements) – matching artists
            albums (list of Album elements) – matching albums
        '''

        logger.info("Searching Plex for track '%s'", query)
        if query is None:
            logger.debug('Ignored search without query')
            return SearchResult(uri='plex:search')


        if 'uri' in query and False: # TODO add uri limiting
            pass
        else:
            search_query = ' '.join(query.values()[0])

        search_uri = 'plex:search:%s' % urllib.quote(search_query.encode('utf-8'))
        logger.info("Searching Plex with query '%s'", search_query)

        artists = []
        tracks = []
        albums = []
        for hit in self.plex.searchAudio(search_query):
            logger.debug('Got plex hit from query "%s": %s', search_query, hit)
            if isinstance(hit, plexaudio.Artist):
                artists.append(wrap_artist(hit, self.backend.plex_uri))
            elif isinstance(hit, plexaudio.Track):
                tracks.append(wrap_track(hit, self.backend.plex_uri))
            elif isinstance(hit, plexaudio.Album):
                albums.append(wrap_album(hit, self.backend.plex_uri, self.backend.resolve_uri))


        logger.debug("Got results: %s, %s, %s", artists, tracks, albums)

        return SearchResult(
            uri=search_uri,
            tracks=tracks,
            artists=artists,
            albums=albums
        )


def wrap_track(plextrack, plex_uri_method):
    '''Wrap a plex search result in mopidy.model.track'''
    return Track(uri=plex_uri_method(plextrack.ratingKey, 'plex:track'),
                 name=plextrack.title,
                 artists=[Artist(uri=plex_uri_method(plextrack.grandparentKey, 'plex:artist'),
                                 name=plextrack.grandparentTitle)],
                 album=Album(uri=plex_uri_method(plextrack.parentKey, 'plex:album'),
                             name=plextrack.parentTitle),
                 track_no=None, #plextrack.index,
                 length=plextrack.duration,
                 # TODO: bitrate=plextrack.media.bitrate,
                 comment=plextrack.summary
                )



def wrap_artist(plexartist, plex_uri_method):
    '''Wrap a plex search result in mopidy.model.artist'''
    return Artist(uri=plex_uri_method(plexartist.ratingKey, 'plex:artist'),
                  name=plexartist.title)



def wrap_album(plexalbum, plex_uri_method, resolve_uri_method):
    '''Wrap a plex search result in mopidy.model.album'''
    return Album(uri=plex_uri_method(plexalbum.ratingKey, 'plex:album'),
                 name=plexalbum.title,
                 artists=[Artist(uri=plex_uri_method(plexalbum.parentKey, 'plex:artist'),
                                 name=plexalbum.parentTitle)],
                 num_tracks=plexalbum.leafCount,
                 num_discs=None,
                 date=str(plexalbum.year),
                 images=[resolve_uri_method(plexalbum.thumb),
                         resolve_uri_method(plexalbum.art)]
                )

