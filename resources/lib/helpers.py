from xbmcswift2 import actions

from rhapsody import exceptions
from rhapsody.api import API
from rhapsody.cache import Base as BaseCache
from rhapsody.models.common import Image


class Helpers:
    class Cache(BaseCache):
        def __init__(self, plugin):
            self._plugin = plugin
            self.storages = {}

        def get_storage(self, timeout):
            timeout = int(timeout / 60)
            if timeout not in self.storages:
                self.storages[timeout] = self._plugin.get_storage('rhapsody.{0:d}'.format(timeout), TTL=timeout)
            return self.storages[timeout]

        def get(self, key, timeout):
            storage = self.get_storage(timeout)
            return storage.get(key)

        def set(self, key, value, timeout):
            storage = self.get_storage(timeout)
            storage[key] = value

    def __init__(self, plugin):
        self._plugin = plugin
        self._cache = plugin.get_storage('helpers', TTL=5)
        self._api = self._get_api()

    def get_artist_item(self, artist, in_library=False):
        item = {
            'label': artist.name,
            'thumbnail': Image.get_url(Image.TYPE_ARTIST, artist.id, Image.SIZE_ARTIST_ORIGINAL),
            'properties': {
                'fanart_image': Image.get_url(Image.TYPE_ARTIST, artist.id, Image.SIZE_ARTIST_ORIGINAL),
            },
            'context_menu': [],
        }
        if in_library:
            item['path'] = self._plugin.url_for('artists_library_albums', artist_id=artist.id)
            item['context_menu'].append((
                self._plugin.get_string(30217),
                actions.update_view(self._plugin.url_for('artists_library_remove', artist_id=artist.id))))
        else:
            item['path'] = self._plugin.url_for('artists_detail', artist_id=artist.id)
            item['context_menu'].append((
                self._plugin.get_string(30215),
                actions.background(self._plugin.url_for('artists_library_add', artist_id=artist.id))))
        return item

    def get_album_item(self, album, show_artist=True, in_library=False, library_artist_id=None):
        if show_artist:
            label = album.artist.name + ' - ' + album.name + ' (' + str(album.get_release_date().year) + ')'
        else:
            label = album.name + ' (' + str(album.get_release_date().year) + ')'
        item = {
            'label': label,
            'thumbnail': Image.get_url(Image.TYPE_ALBUM, album.id, Image.SIZE_ALBUM_ORIGINAL),
            'properties': {
                'fanart_image': Image.get_url(Image.TYPE_ARTIST, album.artist.id, Image.SIZE_ARTIST_ORIGINAL),
            },
            'context_menu': []
        }
        item['context_menu'].append((
            self._plugin.get_string(30255).format(album.artist.name),
            actions.update_view(self._plugin.url_for('artists_detail', artist_id=album.artist.id))
        ))
        if in_library:
            item['path'] = self._plugin.url_for('albums_library_tracks', album_id=album.id)
            if library_artist_id is None:
                action = actions.update_view(self._plugin.url_for('albums_library_remove',
                                                                  album_id=album.id))
            else:
                action = actions.update_view(self._plugin.url_for('artists_library_albums_remove',
                                                                  artist_id=library_artist_id,
                                                                  album_id=album.id))
            item['context_menu'].append((self._plugin.get_string(30217), action))
        else:
            item['path'] = self._plugin.url_for('albums_detail', album_id=album.id)
            item['context_menu'].append((
                self._plugin.get_string(30215),
                actions.background(self._plugin.url_for('albums_library_add', album_id=album.id))))
        return item

    def get_genre_item(self, genre):
        item = {
            'label': genre.name,
            'path': self._plugin.url_for('genres_detail', genre_id=genre.id),
            'thumbnail': Image.get_url(Image.TYPE_GENRE, genre.id, Image.SIZE_GENRE_ORIGINAL),
            'properties': {
                'fanart_image': Image.get_url(Image.TYPE_GENRE, genre.id, Image.SIZE_GENRE_ORIGINAL),
            }
        }
        return item

    def get_playlist_item(self, playlist, in_library=False):
        item = {
            'label': playlist.name,
            'path': self._plugin.url_for('playlists_detail', playlist_id=playlist.id),
            'thumbnail': Image.get_url(Image.TYPE_PLAYLIST, playlist.id, Image.SIZE_PLAYLIST_ORIGINAL),
            'properties': {
                'fanart_image': Image.get_url(Image.TYPE_PLAYLIST, playlist.id, Image.SIZE_PLAYLIST_ORIGINAL),
            }
        }
        if in_library:
            item['context_menu'] = [
                (
                    self._plugin.get_string(30251),
                    actions.update_view(self._plugin.url_for('playlists_library_rename', playlist_id=playlist.id))
                ),
                (
                    self._plugin.get_string(30252),
                    actions.update_view(self._plugin.url_for('playlists_library_remove', playlist_id=playlist.id))
                )
            ]
        return item

    def get_track_item(self, track, show_artist=True, in_library=False, in_favorites=False,
                       in_playlists=False, playlist_id=None, library_album_id=None):
        if show_artist:
            label = track.artist.name + ' - ' + track.name
        else:
            label = track.name
        item = {
            'label': label,
            'is_playable': True,
            'info': {
                'title': track.name,
                'artist': track.artist.name,
                'album': track.album.name,
                'duration': track.duration
            },
            'thumbnail': Image.get_url(Image.TYPE_ALBUM, track.album.id, Image.SIZE_ALBUM_ORIGINAL),
            'properties': {
                'fanart_image': Image.get_url(Image.TYPE_ARTIST, track.artist.id, Image.SIZE_ARTIST_ORIGINAL),
            },
            'context_menu': []
        }
        item['context_menu'].append((
            self._plugin.get_string(30255).format(track.artist.name),
            actions.update_view(self._plugin.url_for('artists_detail', artist_id=track.artist.id))
        ))
        if in_library:
            if library_album_id is None:
                action = actions.update_view(self._plugin.url_for('tracks_library_remove',
                                                                  track_id=track.id))
            else:
                action = actions.update_view(self._plugin.url_for('albums_library_tracks_remove',
                                                                  track_id=track.id,
                                                                  album_id=library_album_id))
            item['context_menu'].append((self._plugin.get_string(30217), action))
        else:
            item['context_menu'].append((
                self._plugin.get_string(30215),
                actions.background(self._plugin.url_for('tracks_library_add', track_id=track.id))))
        if in_favorites:
            item['context_menu'].append((
                self._plugin.get_string(30218),
                actions.update_view(self._plugin.url_for('favorites_remove', track_id=track.id))))
        else:
            item['context_menu'].append((
                self._plugin.get_string(30216),
                actions.background(self._plugin.url_for('favorites_add', track_id=track.id))))
        if in_playlists:
            item['context_menu'].append((
                self._plugin.get_string(30254),
                actions.update_view(self._plugin.url_for('playlists_library_remove_track',
                                                         track_id=track.id, playlist_id=playlist_id))))
        else:
            playlists = self._cache.get('playlists', None)
            if playlists is None:
                playlists = self._api.library.playlists()
                self._cache['playlists'] = playlists
            for playlist in playlists:
                item['context_menu'].append((
                    self._plugin.get_string(30253).format(playlist.name),
                    actions.background(self._plugin.url_for('playlists_library_add_track',
                                                            track_id=track.id, playlist_id=playlist.id))))

        item['path'] = self._plugin.url_for(
                'play',
                track_id=track.id,
                album_id=track.album.id,
                duration=track.duration)
        return item

    def refresh_playlists(self):
        playlists = self._api.library.playlists()
        self._cache['playlists'] = playlists

    def _get_api(self):
        api_key = self._plugin.get_setting('api_key', converter=unicode)
        api_secret = self._plugin.get_setting('api_secret', converter=unicode)
        rhapsody = API(api_key, api_secret, cache_instance=Helpers.Cache(self._plugin))

        try:
            username = self._plugin.get_setting('username', converter=unicode)
            password = self._plugin.get_setting('password', converter=unicode)
            rhapsody.login(username, password)
        except exceptions.AuthenticationError:
            self._plugin.notify(self._plugin.get_string(30100).encode('utf-8'))
            self._plugin.open_settings()
            exit()

        return rhapsody

    def get_api(self):
        return self._api
