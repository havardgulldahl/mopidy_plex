# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pykka
from mopidy import backend
from mopidy.models import Playlist, Ref

import mopidy_plex
from mopidy_plex import logger


class PlexPlaylistsProvider(backend.PlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(PlexPlaylistsProvider, self).__init__(*args, **kwargs)
        self.plex = self.backend.plex


    def as_list(self):
        '''Get a list of the currently available playlists.

        Returns a list of `mopidy.models.Ref` objects referring to the playlists.
        In other words, no information about the playlists’ content is given.'''
        logger.debug('Playlist: as_list')
        for l in self.plex.playlists(playlisttype='audio'):
            yield Ref(uri='plex:playlist:{}'.format(l.ratingKey),
                      name=l.title)

    def create(self, name):
        '''Create a new empty playlist with the given name.

        Returns a new playlist with the given name and an URI.'''
        logger.debug('Playlist: create %r', name)
        pass


    def delete(self, uri):
        '''Delete playlist identified by the URI.'''
        logger.debug('Playlist: delete %r', uri)
        pass

    def get_items(self, uri):
        '''Get the items in a playlist specified by uri.

        Returns a list of Ref objects referring to the playlist’s items.

        If a playlist with the given uri doesn’t exist, it returns None.'''
        logger.debug('Playlist: get_items %r', uri)
        rx = re.compile(r'plex:playlist:(?P<plid>?\d+)').match(uri)
        if rx is None:
            return None

        return [Ref.track(uri='plex:track:{}'.format(item.ratingKey), name=item.title for item in
                          plexaudio.list_items(self.plex, '/playlists/{}/items'.format(rx.groups('plid'))))]


    def lookup(self, uri):
        '''Lookup playlist with given URI in both the set of playlists and in any other playlist source.

        Returns the playlists or None if not found.'''
        pass

    def refresh(self):
        '''Refresh the playlists in playlists.'''
        logger.debug('Refresh')
        pass

    def save(self, playlist):
        '''Save the given playlist.

        The playlist must have an uri attribute set. To create a new playlist with an URI, use create().

        Returns the saved playlist or None on failure.

          Parameters:	playlist (mopidy.models.Playlist) – the playlist to save
          Return type:	mopidy.models.Playlist or None
        '''
        logger.debug('Playlist: save %r', playlist)
        pass