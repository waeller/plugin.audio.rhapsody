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

    def get_album_item(self, album, show_artist=True):
        if show_artist:
            label = album.artist.name + ' - ' + album.name + ' (' + str(album.get_release_date().year) + ')'
        else:
            label = album.name + ' (' + str(album.get_release_date().year) + ')'
        return {
            'label': label,
            'path': self._plugin.url_for('albums_detail', album_id=album.id),
            'thumbnail': album.images[0].url
        }

    def get_track_item(self, track, album=None):
        item = {
            'label': track.name,
            'is_playable': True,
            'info': {
                'title': track.name,
                'artist': track.artist.name,
                'album': track.album.name,
                'duration': track.duration
            }
        }
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
            self._plugin.notify(_(30100).encode('utf-8'))
            self._plugin.open_settings()
            exit()

        return rhapsody