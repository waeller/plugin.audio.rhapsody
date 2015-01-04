import json


class Library(object):
    def __init__(self, api):
        self._api = api

    def artists(self, limit=None, offset=None):
        from rhapsody.models import artists

        return self._api.get_list(artists.List, 'me/library/artists', limit, offset, cache_timeout=None)

    def albums(self, limit=None, offset=None):
        from rhapsody.models import albums

        return self._api.get_list(albums.List, 'me/library/albums', limit, offset, cache_timeout=None)

    def tracks(self, limit=None, offset=None):
        from rhapsody.models import tracks

        return self._api.get_list(tracks.List, 'me/library/tracks', limit, offset, cache_timeout=None)

    def artist_albums(self, artist_id, limit=None, offset=None):
        from rhapsody.models import albums

        return self._api.get_list(albums.List, 'me/library/artists/' + artist_id + '/albums', limit, offset,
                                  cache_timeout=None)

    def artist_tracks(self, artist_id, limit=None, offset=None):
        from rhapsody.models import tracks

        return self._api.get_list(tracks.List, 'me/library/artists/' + artist_id + '/tracks', limit, offset,
                                  cache_timeout=None)

    def album_tracks(self, album_id):
        album = self._api.albums.detail(album_id)
        artist_tracks = [x.id for x in self.artist_tracks(album.artist.id)]
        tracks = []
        for track in album.tracks:
            if track.id in artist_tracks:
                tracks.append(track)
        return tracks

    def recent_artists(self, limit=None, offset=None):
        from rhapsody.models import artists

        return self._api.get_list(artists.List, 'me/recent/artists', limit, offset, cache_timeout=None)

    def recent_tracks(self, limit=None, offset=None):
        from rhapsody.models import tracks

        return self._api.get_list(tracks.List, 'me/listens', limit, offset, cache_timeout=None)

    def playlists(self, limit=None, offset=None):
        from rhapsody.models import playlists

        return self._api.get_list(playlists.List, 'me/playlists', limit, offset, cache_timeout=None)

    def playlist(self, playlist_id):
        from rhapsody.models import playlists

        return self._api.get_detail(playlists.Detail, 'me/playlists', playlist_id, cache_timeout=None)

    def favorites(self, limit=None, offset=None):
        from rhapsody.models import tracks

        return self._api.get_list(tracks.Detail, 'me/favorites', limit, offset, cache_timeout=None)

    def add_artist(self, artist_id):
        for album in self._api.artists.albums(artist_id):
            if album.artist.id == artist_id:
                self.add_album(album.id)

    def remove_artist(self, artist_id):
        for album in self.artist_albums(artist_id):
            self.remove_album(album.id)

    def add_album(self, album_id):
        data = {'id': album_id}
        self._api.post('me/library/albums', json.dumps(data), headers={'Content-Type': 'application/json'})

    def remove_album(self, album_id):
        self._api.delete('me/library/albums/' + album_id)

    def add_track(self, track_id):
        data = {'id': track_id}
        self._api.post('me/library/tracks', json.dumps(data), headers={'Content-Type': 'application/json'})

    def remove_track(self, track_id):
        self._api.delete('me/library/tracks/' + track_id)

    def add_favorite(self, track_id):
        data = {'favorites': [{'id': track_id}]}
        self._api.put('me/favorites', json.dumps(data), headers={'Content-Type': 'application/json'})

    def remove_favorite(self, track_id):
        self._api.delete('me/favorites/' + track_id)

    def add_playlist(self, playlist_name):
        data = {'name': playlist_name}
        self._api.post('me/playlists', json.dumps(data), headers={'Content-Type': 'application/json'})

    def rename_playlist(self, playlist_id, playlist_name):
        data = {'name': playlist_name}
        self._api.put('me/playlists/' + playlist_id, json.dumps(data), headers={'Content-Type': 'application/json'})

    def remove_playlist(self, playlist_id):
        self._api.delete('me/playlists/' + playlist_id)

    def add_track_to_playlist(self, track_id, playlist_id):
        data = {'id': track_id}
        self._api.post('me/playlists/' + playlist_id + '/tracks', json.dumps(data),
                       headers={'Content-Type': 'application/json'})

    def remove_track_from_playlist(self, track_id, playlist_id):
        playlist = self.playlist(playlist_id)
        track_ids = [x.id for x in playlist.tracks]
        if track_id in track_ids:
            track_ids.remove(track_id)
        data = {'id': [x for x in track_ids]}
        # TODO: This call sometimes fails silently so we simply call it 3 times. Definitely needs a better solution
        for x in range(3):
            self._api.put('me/playlists/' + playlist_id + '/tracks', json.dumps(data),
                           headers={'Content-Type': 'application/json'})