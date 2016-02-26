class Search(object):
    class Result(object):
        def __init__(self, data):
            if 'id' in data:
                if data['id'].startswith('Art.'):
                    from rhapsody.models import artists
                    self.type = 'artist'
                    self.data = artists.List(data)
                if data['id'].startswith('Alb.'):
                    from rhapsody.models import albums
                    self.type = 'album'
                    self.data = albums.List(data)
                if data['id'].startswith('Tra.'):
                    from rhapsody.models import tracks
                    self.type = 'track'
                    self.data = tracks.List(data)
            else:
                self.type = 'unknown'
                self.data = None

    def __init__(self, api):
        self._api = api

    def fulltext(self, query, content_type=None, limit=None, offset=None):
        return self._api.get_list(Search.Result, 'search', limit, offset, params={
            'q': query,
            'type': content_type
        })

    def typeahead(self, query, content_type=None, limit=None, offset=None):
        return self._api.get_list(Search.Result, 'search/typeahead', limit, offset, params={
            'q': query,
            'type': content_type
        })
