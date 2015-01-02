from metadata import *


class Base(object):
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']


class List(Base):
    def __init__(self, data):
        super(List, self).__init__(data)


class Detail(Base):
    def __init__(self, data):
        super(Detail, self).__init__(data)


class Genres(MetadataList, MetadataDetail):
    url_base = 'genres'
    list_class = List
    detail_class = Detail
