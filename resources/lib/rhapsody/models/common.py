from metadata import *


class Image(MetadataDetail.Detail, object):
    SIZE_TINY = '70x70'
    SIZE_SMALL = '170x170'
    SIZE_MEDIUM = '200x200'
    SIZE_LARGE = '300x300'
    SIZE_ORIGINAL = '500x500'

    def __init__(self, data):
        super(Image, self).__init__(data)
        self.width = data['width']
        self.height = data['height']
        self.url = data['url']

    def get_url(self, size=SIZE_MEDIUM):
        return self.url.replace('%sx%s' % (self.width, self.height), size)