from WebRequestHandler import WebRequestHandler
import re
#import itertools
import wikipedia
from collections import defaultdict, namedtuple, OrderedDict
from itertools import chain, combinations
from nltk.tokenize import sent_tokenize
from unidecode import unidecode
import difflib

from WebRequestHandler import GoogleApiHandler

#Detailer
#cache the geo_center/limits, do not pass the place
class GooglePlacesDetailer(GoogleApiHandler):
    '''Gets details of any Google place with address and geo verification 
    Requires:
    city - string
    country - string
    geo_center - namedtuple Location: ('lat': _, 'lng': _)
    geo_bounds - namedtuple Bounds: ('NE': Location, 'SW': Location)
    '''

    def __init__(self, city, country, geo_center, geo_bounds):
        super().__init__()
        self.city = city.lower()
        self.country = country.lower()
        self.geo_center = geo_center
        self.geo_bounds = geo_bounds
        self.kg_score_limit = 1000
    
    def address_verify(self, result):
        address_components = [component.get('long_name').lower() for component in result['result']['address_components']]
        # Could use some improvement like what is used in wikipedia search verification
        if self.city in address_components or self.country in address_components:
            return True
        else:
            return False

    # following two methods may better belong in Place.py
    def geo_verify(self, result):
        #this isn't necessary, but I like namedtuples
        Location = namedtuple('Location', ['lat', 'lng'])
        loc_dict = result['result'].get('geometry', {}).get('location')
        place_loc = Location(loc_dict['lat'], loc_dict['lng'])
        # latitude check, breaks at the poles but we won't be going there
        if place_loc.lat < self.geo_bounds.NE.lat and place_loc.lat > self.geo_bounds.SW.lat:
            #split longitude check, probably unecessary but better safe than sorry
            if self.geo_bounds.NE.lng > self.geo_bounds.SW.lng:
                if place_loc.lng < self.geo_bounds.NE.lng and place_loc.lng > self.geo_bounds.SW.lat:
                    return True
            else:
                if place_loc.lng > self.geo_bounds.NE.lng and place_loc.lng < self.geo_bounds.SW.lat:
                    return True
        return False
    
    def fetch_place_data(self, name):
        lat, lng = self.geo_center.lat, self.geo_center.lng
        api_url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
        params = 'input={}&inputtype=textquery&locationbias=point:{},{}&key={}'\
            .format(name, str(lat), str(lng), self.api_keys['google']) 
        result = self.call_api(api_url, params)
        candidates = result['candidates']
        for candidate in candidates:
            place_id = candidate['place_id']
            result = self.fetch_place_id_data(place_id)
            if self.address_verify(result) or self.geo_verify(result):
                return result
            else:
                print(f'Failed geo-verification and address verification')
        return None
    
    def fetch_place_id_data(self, place_id):
        api_url = 'https://maps.googleapis.com/maps/api/place/details/json'
        params = 'place_id={}&key={}'.format(place_id, self.api_keys['google'])
        result = self.call_api(api_url, params)
        return result

    def parse_place_id_data(self, place, result):
        raise NotImplementedError
    
    def fetch_place_photo(self, photo_reference):
        api_url = 'https://maps.googleapis.com/maps/api/place/photo'
        params = 'photoreference={}&maxheight=1600&maxwidth=1600&key={}'\
            .format(photo_reference, self.api_keys['google'])
        r = self.fetch_url_data(api_url + '?' + params)
        return r.url


class GoogleSightsDetailer(GooglePlacesDetailer):
    parenthesis_content = re.compile(r'\s\([^)]*\)')

    def __init__(self, city, country, geo_center, geo_bounds):
        '''Initialization creates dictionary for later translation to Dataframe objects'''
        super().__init__(city, country, geo_center, geo_bounds)

    def detail(self, place):
        '''Given name of place, calls class methods to retrieve information 
        using Google Services.
        Input: Place object
        Returns Place object'''
        try:
            places_result = self.fetch_place_data(place.name)
            photo_ref = self.parse_place_id_data(place, places_result)
            kg_result = self.fetch_kg_data(place.name)
            self.parse_kg_data(place, kg_result)
            if not place.description:
                place.description = self.get_description(place)
        except SearchError:
            pass
        return place

    def parse_place_id_data(self, place, result):
        '''Parses information obtained from fetched place id data.
        Retrieves the following:
        Formatted Address
        Formatted Phone Number
        International Phone Number
        Tags
        Location
        Rating
        Opening Hours
        City
        Country
        '''
        try:
            result = result.get('result')
        except:
            return place
        place.place_id = result.get('place_id')
        place.address = result.get('formatted_address')
        place.address_components = result.get('address_components', [])
        place.phone_num_dom = result.get('formatted_phone_number')
        place.phone_num_intl = result.get('international_phone_number')
        place.append_tags(result.get('types',[]))
        place.location = result.get('geometry', {}).get('location')
        place.rating = result.get('rating')
        place.opening_hours_text = result.get('opening_hours', {}).get('weekday_text', [])
        place.opening_hours = result.get('opening_hours', {}).get('periods', [])
        photos_arr = result.get('photos')
        if photos_arr:
            place.photo = {
                'url': photos_arr[0].get('photo_reference'),
                'attributions': photos_arr[0].get('html_attributions')
            }
        return place

    def fetch_kg_data(self, query):
        '''Fetches information from Google Knowledge Graph'''
        api_url = 'https://kgsearch.googleapis.com/v1/entities:search'
        params = 'query={}&types=Place&key={}'.format(query, self.api_keys['google'])
        kg_result = self.call_api(api_url, params)
        return kg_result

    def parse_kg_data(self, place, kg_json):
        '''Parses information from Google knowledge graph. 
        Retrieves the following:
        Category (via method get_category)
        Tags (set object)
        Detailed Description
        '''
        kg_data = kg_json.get('itemListElement')
        if kg_data:
            results = kg_data[0]['result']
            if results['name'] == place.name:
                place.category = self.get_category(results.get('description'))
                place.append_tags(results.get('@type', []))
                place.description = self.fill_description_dict(
                    results.get('detailedDescription', {}).get('articleBody'),
                    results.get('detailedDescription', {}).get('url')
                )
                if not place.photo:
                    print('Adding photo from kg')
                    r = self.fetch_url_data(results.get('image', {}).get('url'))
                    try:
                        image_urls = r.html.xpath('//*[@id="file"]/a')
                        place.photo = {
                            'url': image_urls[0].links.pop(),
                            'attributions': ['<a href="{}">Wikimedia</a>'.format(results.get('image', {}).get('url'))]
                        }
                    except IndexError:
                        pass
                    
        return place

    def get_category(self, descrip):
        '''Given description, gets category of sight
        Retrieves the following:
        Category
        '''
        try:
            [category, place]= descrip.split(' in ')
        except (ValueError, AttributeError):
            category = 'Area'
        return category
    
    def get_description(self, place):
        '''
        Generator object for getting wikipedia articles. 
        Returns dict {'description': <String>, 'src': <String>}
        '''
        
        valid_page = False
        page_name = place.name
        previous_results = []
        while not valid_page:
            try:
                #Immediately try suggested page
                wiki = wikipedia.WikipediaPage(page_name)
                print(f'Went to {wiki.title}')
                valid_page = True
            except wikipedia.DisambiguationError as e:
                #DisambiguationError options are not sorted by relevancy. Requires self-sort
                print(e)
                options = self.relevancy_filter([place.name, place.city], e.options)
                print(f'DisambiguationError. Given options {options}. Choosing {options[0]}.')
                page_name = options[0]
            except wikipedia.PageError:
                #Page errors are sorted by relevancy, but it could be that the page does not exist
                print('Page error')
                search_results, suggestion = wikipedia.search(place.name, suggestion=True)
                if suggestion:
                    print('First index is a suggestion')
                    suggestion = ' '.join([word.capitalize() for word in suggestion.split()])
                    search_results = [suggestion] + search_results
                relevant = self.relevancy_filter([place.name, place.city], search_results)
                if not relevant or (not relevant[0] in search_results[:2]):
                    #If there are no relevant items or the most relevant item is not in the top 2 of wikipedia's results, require manual input
                    print(relevant)
                    print(search_results)
                    i = int(input(f'Choose an index: '))
                    try:
                        page_name = search_results[i]
                    except:
                        print('Irrelevant index, leaving description empty')
                        return self.fill_description_dict('', '')
                else:
                    #check if we are in a loop
                    print(f'previous results: {previous_results}')
                    print(f'Current results: {search_results}')
                    if previous_results == search_results:
                        print('Loop detected. Trying next index of relevant items if possible')
                        try:
                            page_name = relevant[1]
                        except IndexError:
                            try:
                                page_name = search_results[1]
                            except IndexError:
                                print('Irrelevant index, leaving description empty')
                                return self.fill_description_dict('', '')
                    else:
                        previous_results = search_results
                        page_name = relevant[0]
        #Usually only first two sentences are relevant
        sentences = sent_tokenize(wiki.summary)[:2]
        description = re.sub(GoogleSightsDetailer.parenthesis_content, '', ' '.join(sentences))
        return self.fill_description_dict(description, wiki.url)
    
    def fill_description_dict(self, description, src):
        return {
            'description': description,
            'src': src
        }

    def relevancy_filter(self, queries, results):
        priority_dict = {}
        for result in results:
            word_list = list(chain(*[words.split() for words in queries]))
            matches = self.stringsubset(word_list, result.split())
            if matches:
                if priority_dict.get(matches):
                    priority_dict[matches].append(result)
                else:
                    priority_dict[matches] = [result]
        priority_list = [val for key, val in sorted(priority_dict.items(), key=lambda x: x[0], reverse=True)]
        #Sort by difflib relevancy. Possible that the following is enough? No need for match-based string subset ordering?
        relevancy_list = [sorted(l, key=lambda seq: difflib.SequenceMatcher(None, seq, queries[0]).ratio(), reverse=True) for l in priority_list]
        return list(chain(*relevancy_list))

    def stringsubset(self, a, b):
        '''
        Returns number of substring matches of strings in A and strings in B
        '''
        #filter diacritics
        if isinstance(a, str):
            a = a.split()
        a = [unidecode(word).lower().replace('-', '') for word in a]
        if isinstance(b, str):
            b = b.split()
        b = [unidecode(word).lower().replace('-', '') for word in b]
        matches = 0
        for word_a in a:
            for word_b in b:
                if (word_a in word_b): # or (word_b in word_a):
                    matches += 1
        return matches

    def categorize(self):
        predefined_categories = [
            'Museum', 'Zoo', 'Aquarium', 'Theatre', 'Theme Park', \
            'Market', 'District', 'Tower', 'Bridge', 'Public Art', \
            'Mountain', 'Park', 'Garden', 'Island', 'Lake', 'Beach', \
            'Historical Landmark', 'Religious Landmark', 'Monument', \
            'Novelty']

        #ML for summary/description/article to categorization
        
class SearchError(Exception):
    pass

class GoogleHotelDetailer(GooglePlacesDetailer):
    def __init__(self):
        pass

class GoogleEatsDetailer(GooglePlacesDetailer):
    def __init__(self):
        pass

if __name__=="__main__":
    city = 'kyoto'
    country = 'japan'
    Location = namedtuple('Location', ['lat', 'lng'])
    Bounds = namedtuple('Bounds', ['NE', 'SW'])
    location = Location()
    sight = Sight({'name': 'Fushimi Inari Taisha', 'place_id': 'ChIJIW0uPRUPAWAR6eI6dRzKGns', 'city': city, 'country': country})
    detailer = GoogleSightsDetailer(city, country, location, bounds)