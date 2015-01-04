from xbmcswift2 import actions
from rhapsody.api import API
from rhapsody.cache import Base as BaseCache


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

    def get_artist_item(self, artist, in_library=False):
        item = {
            'label': artist.name,
            'context_menu': []
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

    def get_album_item(self, album, show_artist=True, in_library=False):
        if show_artist:
            label = album.artist.name + ' - ' + album.name + ' (' + str(album.get_release_date().year) + ')'
        else:
            label = album.name + ' (' + str(album.get_release_date().year) + ')'
        item = {
            'label': label,
            'thumbnail': album.images[0].url,
            'context_menu': []
        }
        if in_library:
            item['path'] = self._plugin.url_for('albums_library_tracks', album_id=album.id)
            item['context_menu'].append((
                self._plugin.get_string(30217),
                actions.update_view(self._plugin.url_for('albums_library_remove', album_id=album.id))))
        else:
            item['path'] = self._plugin.url_for('albums_detail', album_id=album.id)
            item['context_menu'].append((
                self._plugin.get_string(30215),
                actions.background(self._plugin.url_for('albums_library_add', album_id=album.id))))
        return item

    def get_track_item(self, track, album=None, show_artist=True, in_library=False, in_favorites=False):
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
            'context_menu': []
        }
        if in_library:
            item['context_menu'].append((
                self._plugin.get_string(30217),
                actions.update_view(self._plugin.url_for('tracks_library_remove', track_id=track.id))))
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
        if album is None:
            thumbnail_missing = True
        else:
            thumbnail_missing = False
            item['thumbnail'] = album.images[0].url
            # item['info']['tracknumber'] = [i for i, j in enumerate(album.tracks) if j.id == track.id][0] + 1
        item['path'] = self._plugin.url_for(
            'play',
            track_id=track.id,
            album_id=track.album.id,
            duration=track.duration,
            thumbnail_missing=thumbnail_missing)
        return item

    def get_api(self):
        api_key = self._plugin.get_setting('api_key', converter=unicode)
        api_secret = self._plugin.get_setting('api_secret', converter=unicode)
        rhapsody = API(api_key, api_secret, cache_instance=Helpers.Cache(self._plugin))

        try:
            username = self._plugin.get_setting('username', converter=unicode)
            password = self._plugin.get_setting('password', converter=unicode)
            rhapsody.login(username, password)
        except rhapsody.AuthenticationError:
            self._plugin.notify(self._plugin.get_string(30100).encode('utf-8'))
            self._plugin.open_settings()
            exit()

        return rhapsody