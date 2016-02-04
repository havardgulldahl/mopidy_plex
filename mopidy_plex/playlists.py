# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from mopidy import backend
from mopidy.models import Ref, Playlist

from plexapi import audio as plexaudio, playlist as plexplaylist

from mopidy_plex import logger
from .library import wrap_track


class PlexPlaylistsProvider(backend.PlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(PlexPlaylistsProvider, self).__init__(*args, **kwargs)
        self.plex = self.backend.plex


    def as_list(self):
        '''Get a list of the currently available playlists.

        Returns a list of `mopidy.models.Ref` objects referring to the playlists.
        In other words, no information about the playlists’ content is given.'''
        logger.debug('Playlist: as_list')
        return [Ref(uri='plex:playlist:{}'.format(playlist.ratingKey), name=playlist.title)
                for playlist in self.plex.playlists(playlisttype='audio')]


    def create(self, name):
        '''Create a new empty playlist with the given name.

        Returns a new playlist with the given name and an URI.'''
        logger.debug('Playlist: create %r', name)



    def delete(self, uri):
        '''Delete playlist identified by the URI.'''
        logger.debug('Playlist: delete %r', uri)


    def get_items(self, uri):
        '''Get the items in a playlist specified by uri.

        Returns a list of Ref objects referring to the playlist’s items.

        If a playlist with the given uri doesn’t exist, it returns None.


          Return type:	list of mopidy.models.Ref, or None

        '''
        logger.debug('Playlist: get_items %r', uri)
        _rx = re.compile(r'plex:playlist:(?P<plid>\d+)').match(uri)
        if _rx is None:
            return None

        def wrap_ref(item):
            return Ref.track(uri='plex:track:{}'.format(item.ratingKey), name=item.title)

        return [wrap_ref(item) for item in
                plexaudio.list_items(self.plex, '/playlists/{}/items'.format(_rx.groups('plid')))]


    def lookup(self, uri):
        '''Lookup playlist with given URI in both the set of playlists and in any other playlist source.

        Returns the playlists or None if not found.


          Parameters:	uri (string) – playlist URI
          Return type:	mopidy.models.Playlist or None

        '''
        logger.debug('Playlist: lookup %r', uri)
        _rx = re.compile(r'plex:playlist:(?P<plid>\d+)').match(uri)
        if _rx is None:
            return None
        plexlist = plexplaylist.list_items(self.plex, '/playlists/{:s}'.format(_rx.groups('plid')))[0]
        PL = Playlist(uri=uri,
                      name=plexlist.title,
                      tracks=[wrap_track(_t, self.plex.plex_uri) for _t in plexlist.tracks()],
                      last_modified=None, # TODO: find this value
                     )
        return PL

    def refresh(self):
        '''Refresh the playlists in playlists.'''
        logger.debug('Refresh')


    def save(self, playlist):
        '''Save the given playlist.

        The playlist must have an uri attribute set. To create a new playlist with an URI, use create().

        Returns the saved playlist or None on failure.

          Parameters:	playlist (mopidy.models.Playlist) – the playlist to save
          Return type:	mopidy.models.Playlist or None
        '''
        logger.debug('Playlist: save %r', playlist)
