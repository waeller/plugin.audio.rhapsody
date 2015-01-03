from datetime import date
from metadata import *


class Base(object):
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']


class List(Base):
    class Type:
        def __init__(self, data):
            self.id = data['id']
            self.name = data['name']

    def __init__(self, data):
        import common
        import artists

        super(List, self).__init__(data)
        self.artist = artists.List(data['artist'])
        self.type = List.Type(data['type'])
        self.images = [common.Image(x) for x in data['images']]
        self.released = data['released']
        
    def get_release_date(self):
        return date.fromtimestamp(self.released / 1000)


class Detail(List):
    def __init__(self, data):
        import tracks

        super(Detail, self).__init__(data)
        self.tracks = [tracks.List(x) for x in data['tracks']]


class Albums(MetadataList, MetadataDetail):
    url_base = 'albums'
    list_class = List
    detail_class = Detail

    def tracks(self, album_id):
        from rhapsody.models import tracks

        return self.list(album_id + '/tracks', model=tracks.List)