from collections import defaultdict, namedtuple
import pandas as pd
import json
import re


# TODO: Need pictures url

class Place:
    def __init__(self, place_dict={}):
        self.tags = set()
        self.update(place_dict)
    
    def to_dict(self, place_dict):
        if isinstance(place_dict, dict):
            pass
        elif isinstance(place_dict, tuple):
            place_dict = place_dict._asdict()
        elif isinstance(place_dict, pd.Series) or isinstance(place_dict, pd.DataFrame):
            place_dict = place_dict.to_dict()
        else:
            raise TypeError
        return place_dict

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        Location = namedtuple('Location', ['lat', 'lng'])
        if isinstance(location, dict):
            self._location = Location(location['lat'], location['lng'])
        elif isinstance(location, tuple) or isinstance(location, list):
            self._location = Location(location[0], location[1])
        else:
            self._location = None

    def update(self, place_dict):
        place_dict = self.to_dict(place_dict)
        self.name = place_dict.get('name')
        self.place_id = place_dict.get('google_places_id')
        self.city = place_dict.get('city')
        self.country = place_dict.get('country')
        self.address = place_dict.get('address')
        self.address_components = place_dict.get('address_components')
        self.location = place_dict.get('location') #self.to_namedtuple(place_dict.get('location'))
        self.rating = place_dict.get('rating')
        self.visit_time = place_dict.get('visit_time')
        self.phone_num_dom = place_dict.get('phone_num_dom')
        self.phone_num_intl = place_dict.get('phone_num_intl')
        self.append_tags(place_dict.get('tags', []))

        if self.address_components and isinstance(self.address_components, str):
            self.address_components = json.loads(self.address_components)
        return place_dict
        
    def append_tags(self, new_tags):
        for i, tag in enumerate(new_tags):
            new_tags[i] = ''.join(['_' + char.lower() if char.isupper() else char for char in tag]).lstrip('_')
        new_tags = set(new_tags)
        self.tags.update(new_tags)

    def as_dict(self):
        place_dict = defaultdict()
        weak_private = re.compile('_[^_].*')
        #for each place property, serialize anything that isn't a string
        place_dict = vars(self)
        '''
        place_dict.update({'name': self.name, 'place_id': self.place_id, 'city': self.city, 'country': self.country, 'address': self.address, \
                            'address_components': self.address_components, 'location': self.location, 'rating': self.rating, 'visit_time': self.visit_time, \
                            'phone_num_dom': self.phone_num_dom, 'phone_num_intl': self.phone_num_intl, 'tags': self.tags})
        '''
        place_dict['tags'] = list(place_dict['tags'])
        place_dict['address_components'] = json.dumps(place_dict['address_components'])
        place_dict['opening_hours'] = json.dumps(place_dict['opening_hours'])
        keys_to_change = [key for key in place_dict.keys() if re.match(weak_private, key)]
        for key in keys_to_change:
            place_dict[key[1:]] = place_dict.pop(key)
        return place_dict

class Sight(Place):
    def __init__(self, sight_dict={}):
        super().__init__(sight_dict)
        self.update(sight_dict)
    
    def update(self, sight_dict):
        super().update(sight_dict)
        sight_dict = self.to_dict(sight_dict)
        self.category = sight_dict.get('category')
        self.descrip_title = sight_dict.get('descrip_title')
        self.descrip_long = sight_dict.get('descrip_long')
        self.opening_hours = sight_dict.get('opening_hours')
        self.opening_hours_text = sight_dict.get('opening_hours_text')
        if self.opening_hours and isinstance(self.opening_hours, str):
            self.opening_hours = json.loads(self.opening_hours)

class Hotel(Place):
    def __init__(self, hotel_dict={}):
        super().__init__(hotel_dict)
        self.update(hotel_dict)
    
    def update(self, hotel_dict):
        super().update(hotel_dict)

class Eatery(Place):
    def __init__(self, eatery_dict={}):
        super().__init__(eatery_dict)
        self.update(eatery_dict)

    def update(self, eatery_dict):
        super().update(eatery_dict)

if __name__=='__main__':
    sight = Sight()

    sight.location = {'lat': 123, 'lng': 345}
    print(sight.location)
    print(sight.as_dict())
