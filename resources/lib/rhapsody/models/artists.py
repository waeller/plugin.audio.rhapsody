from metadata import *


class Base(object):
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']

    def get_station_id(self):
        return self.id.lower().replace('art.', 'sas.')


class List(Base):
    def __init__(self, data):
        super(List, self).__init__(data)


class Detail(Base):
    def __init__(self, data):
        super(Detail, self).__init__(data)


class Artists(MetadataList, MetadataDetail):
    class Similar(object):
        def __init__(self, data):
            self.contemporaries = [Detail(x) for x in data['contemporaries']]
            self.followers = [Detail(x) for x in data['followers']]
            self.influencers = [Detail(x) for x in data['influencers']]
            self.related = [Detail(x) for x in data['related']]

    url_base = 'artists'
    list_class = List
    detail_class = Detail

    def top(self):
        return self.list('top')

    def albums(self, artist_id):
        import albums

        return self.list(artist_id + '/albums', limit=1000, model=albums.List)

    def similar(self, artist_id):
        return self.detail(artist_id + '/similar', model=Artists.Similar)
