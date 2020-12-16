from collections import defaultdict, namedtuple
import pandas as pd
import json
import re


# TODO: classmethods?

class Place:
    def __init__(self, place_dict={}):
        self.tags = set()
        place_dict = self.to_dict(place_dict)
        self.update(place_dict)           
    
    def __repr__(self):
        output = ''
        place_dict = vars(self)
        for key, value in place_dict.items():
            output += '{} {}: {}\n'.format(key, type(value), value)
        return output

    def to_dict(self, place_dict):
        '''Ensures "place_dict" variable is actually a dict'''
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
        self.place_id = place_dict.get('google_places_id')
        self.name = place_dict.get('name')
        self.city = place_dict.get('city')
        self.country = place_dict.get('country')
        self.address = place_dict.get('address')
        self.address_components = place_dict.get('address_components')
        self.location = place_dict.get('location') #self.to_namedtuple(place_dict.get('location'))
        self.rating = place_dict.get('rating')
        self.visit_time = place_dict.get('visit_time')
        self.phone_num_dom = place_dict.get('phone_num_dom')
        self.phone_num_intl = place_dict.get('phone_num_intl')
        self.photo = place_dict.get('photo')
        self.append_tags(place_dict.get('tags', []))
        self.deserialize(self.address_components, self.photo)
        self.query_terms = place_dict.get('query_terms')
        return place_dict
    
    @classmethod
    def deserialize(cls, *args):
        for arg in args:
            if arg and isinstance(arg, str):
                arg = json.loads(arg)

    def append_tags(self, new_tags):
        for i, tag in enumerate(new_tags):
            new_tags[i] = ''.join(['_' + char.lower() if char.isupper() else char for char in tag]).lstrip('_')
        new_tags = set(new_tags)
        self.tags.update(new_tags)

    def as_dict(self):
        # List of dicts need json serialization
        # Rename private vars
        place_dict = vars(self)
        weak_private = re.compile('_[^_].*')
        place_dict = {(k if not re.match(weak_private,k) else k[1:]):v for (k,v) in place_dict.items()}
        place_dict['tags'] = list(place_dict['tags'])
        place_dict['address_components'] = json.dumps(place_dict['address_components'])
        place_dict['photo'] = json.dumps(place_dict['photo'])
        return place_dict

class Sight(Place):
    def __init__(self, sight_dict={}):
        super().__init__(sight_dict)
        self.update(sight_dict)
    
    def update(self, sight_dict):
        super().update(sight_dict)
        sight_dict = self.to_dict(sight_dict)
        self.category = sight_dict.get('category')
        self.summary = sight_dict.get('summary')
        self.description = sight_dict.get('description')
        self.photo = sight_dict.get('photo')
        self.opening_hours = sight_dict.get('opening_hours')
        self.deserialize(self.description, self.opening_hours)
        self.opening_hours_text = sight_dict.get('opening_hours_text')
    
    def as_dict(self):
        place_dict = super().as_dict()
        place_dict['opening_hours'] = json.dumps(place_dict['opening_hours'])
        place_dict['description'] = json.dumps(place_dict['description'])
        return place_dict

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
