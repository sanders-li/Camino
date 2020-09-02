import pandas as pd
import numpy as np
import os
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import lxml
import json
import time
from collections import defaultdict, namedtuple
from contextlib import suppress
import itertools
import re
from Place import Sight
import wikipedia
from nltk.tokenize import sent_tokenize


# TODO: Implement FourSquareAPI handling

class WebAPIRequestHandler():
    def __init__(self):
        with open('keys.json', 'r') as f:
            self.api_keys = json.loads(f.read())
        self.session = HTMLSession()

    def call_api(self, api_url):
        r = self.fetch_url_data(api_url)
        result = json.loads(r.text)
        if self.response_check(result):
            return result

    def fetch_url_data(self, url):
        print(f'Accessing: {url}')
        r = self.session.get(url)
        if r.status_code == 200:
            return r

    def response_check(self, result):
        '''Translates Google Place API specific text response to a dictionary object'''
        status_error_codes = ["ZERO_RESULTS", "OVER_QUERY_LIMIT", "REQUEST_DENIED", "INVALID_REQUEST", "UNKNOWN_ERROR"]
        with suppress(KeyError):
            if result['error'] or result['status'] in status_error_codes:
                raise IOError
        return True


class GooglePlacesFinder(WebAPIRequestHandler):
    def __init__(self, city, country):
        super().__init__()
        self.city = city.lower()
        self.country = country.lower()
        self.sights_df = pd.DataFrame()
        self.raw_df = pd.DataFrame()
        self.sights_list = []
        self.scraped_sights = defaultdict()
        
    def run(self, url):
        '''
        Input: URL of Google Travel Sights (String)
        Output: Details of all sights using Google services (Pandas Dataframe Object)
        '''
        self.things_to_do_scrape(url)
        #get more detailed information here
        detailer = GoogleSightsDetailer(self.city, self.country)
        count = 0
        for sight in self.scraped_sights.values():
            sight, raw_data = detailer.fill_details(sight)
            row = pd.Series(sight.as_dict())
            self.sights_df = self.sights_df.append(row, ignore_index=True)
            self.sights_list.append(sight.as_dict())
            count += 1
        return self.sights_df
        
    def things_to_do_scrape(self, url):
        '''Given URL of Google Travel Sights, scrapes HTML data for sights.
        Returns list of sights to be parsed for information
        '''
        r = self.fetch_url_data(url)
        xpath = '//*[@id="yDmH0d"]/c-wiz[2]/div/div[2]/div/c-wiz/div/div/div[1]/div[2]/c-wiz/div/div[1]/div/div/div'
        for item in r.html.xpath(xpath):
            name = item.find('.skFvHc.YmWhbc', first=True).text
            descrip = item.find('.nFoFM', first=True).text
            self.scraped_sights[name] = Sight({'name': name, 'descrip_title': descrip, 'city': self.city, 'country': self.country})
        return self.scraped_sights

    def save_df(self, filepath=None):
        if not filepath:
            filepath = os.path.join(os.getcwd(), '{}_{}_sights_df.json'.format(self.city, self.country))
        self.sights_df.to_json(filepath, indent=4)
        print(f'Saved DF to {filepath}')

    def load_df(self, filepath):
        if not filepath:
            filepath = os.path.join(os.getcwd(), '{}_{}_sights_df.json'.format(self.city, self.country))
        self.sights_df = pd.read_json(filepath)
        return self.sights_df

    def save_excel(self, filepath=None):
        if not filepath:
            filepath = os.path.join(os.getcwd(), '{}_{}_sights.xlsx'.format(self.city, self.country))
        self.sights_df.to_excel(filepath)
        print(f'Saved excel to {filepath}')

    def load_excel(self, filepath):
        pd.read_excel('{}_{}_sights.xlsx'.format(self.city, self.country))
        return self.sights_list
        
#cache the geo_center/limits, do not pass the place
class GooglePlacesDetailer(WebAPIRequestHandler):
    def __init__(self, city, country, place=defaultdict(), raw_data=defaultdict()):
        super().__init__()
        self.place = place
        self.raw_data = raw_data
        self.city = city.lower()
        self.country = country.lower()
        self.geo_center, self.geo_limits = self.set_geo_limits()
        self.parenthesis_content = re.compile(r'\s\([^)]*\)')
        self.kg_score_limit = 1000
    
    def set_geo_limits(self):
        target = '{}, {}'.format(self.city, self.country)
        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?input={}&inputtype=textquery&key={}'.format(target, self.api_keys.google)
        result = self.call_api(url)
        location = result['results'][0]['geometry']['location']
        center = self.extract_loc(location)
        viewport = result['results'][0]['geometry']['viewport']
        Bounds = namedtuple('Bounds', ['NE', 'SW'])
        NE_limit = self.extract_loc(viewport['northeast'])
        SW_limit = self.extract_loc(viewport['southwest'])
        return center, Bounds(NE_limit, SW_limit)

    def address_verify(self, result):
        address_components = [component.get('long_name').lower() for component in result['result']['address_components']]
        if self.city in address_components or self.country in address_components:
            return True
        else:
            return False

    # following two methods may better belong in Place.py
    def geo_verify(self, result):
        loc_dict = result['result'].get('geometry', {}).get('location')
        place_loc = self.extract_loc(loc_dict)
        # latitude check, breaks at the poles but we won't be going there
        if place_loc.lat < self.geo_limits.NE.lat and place_loc.lat > self.geo_limits.SW.lat:
            #split longitude check, probably unecessary but better safe than sorry
            if self.geo_limits.NE.lng > self.geo_limits.SW.lng:
                if place_loc.lng < self.geo_limits.NE.lng and place_loc.lng > self.geo_limits.SW.lat:
                    return True
            else:
                if place_loc.lng > self.geo_limits.NE.lng and place_loc.lng < self.geo_limits.SW.lat:
                    return True
        return False
    
    def extract_loc(self, loc_dict):
        Location = namedtuple('Location', ['lat', 'lng'])
        return Location(loc_dict['lat'], loc_dict['lng'])

    def fill_details(self, place):
        pass

    def fetch_place_data(self, name, save_raw=True):
        lat, lng = self.geo_center.lat, self.geo_center.lng
        url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={}&inputtype=textquery&locationbias=point:{},{}&key={}'\
            .format(name, str(lat), str(lng), self.api_key.google) 
        result = self.call_api(url)
        candidates = result['candidates']
        for candidate in candidates:
            place_id = candidate['place_id']
            result = self.fetch_place_id_data(place_id)
            if self.geo_verify(result) or self.address_verify(result):
                return result
            else:
                print(f'Failed geo-verification and addressverification')
        return None
    
    def fetch_place_id_data(self, place_id):
        url = 'https://maps.googleapis.com/maps/api/place/details/json?place_id={}&key={}'.format(place_id, self.api_key.google)
        result = self.call_api(url)
        return result

    def parse_place_id_data(self):
        pass
    
    def fetch_kg_data(self, query, save_raw=True):
        '''Fetches information from Google Knowledge Graph'''
        url = 'https://kgsearch.googleapis.com/v1/entities:search?query={}&types=Place&key={}'.format(query, self.api_key.google)
        kg_result = self.call_api(url)
        if save_raw:
            self.raw_data['google_kg'] = kg_result
        return kg_result

    def parse_kg_data(self):
        pass

    #google search to bring up improved KG data card, parse
    def fetch_kp_data(self, query, save_raw=True):
        url = 'https://google.com/search?{}+{}+{}'.format(query, self.city, self.country)
        r = self.fetch_url_data(url)
        kp_html = r.html
        if save_raw:
            self.raw_data['google_kp_html'] = kp_html
        return kp_html
    
    def parse_kp_data(self):
        pass    


class GoogleSightsDetailer(GooglePlacesDetailer):
    def __init__(self, city, country):
        '''Initialization creates dictionary for later translation to Dataframe objects'''
        super().__init__(city, country)

    def fill_details(self, place):
        '''Given name of place, calls class methods to retrieve information 
        using Google Services.
        Input: Place object
        Returns Place object'''
        self.place = place
        try:
            places_result = self.fetch_place_data(self.place.name)
            self.parse_place_id_data(places_result)
            
            kg_json = self.fetch_kg_data(self.place.name)
            self.parse_kg_data(kg_json)
            self.get_summary(self.place.name)
            #r = self.fetch_kp_data(name)
            #self.parse_kp_data(r)
        except SearchError:
            pass
        place, raw_data = self.place, self.raw_data
        self.place, self.raw_data = defaultdict(), defaultdict()
        return place, raw_data

    def parse_place_id_data(self, result):
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
        result = result.get('result')
        self.place.place_id = result.get('place_id')
        self.place.address = result.get('formatted_address')
        self.place.address_components = result.get('address_components', [])
        self.place.phone_num_dom = result.get('formatted_phone_number')
        self.place.phone_num_intl = result.get('international_phone_number')
        self.place.append_tags(result.get('types',[]))
        self.place.location = result.get('geometry', {}).get('location')
        self.place.rating = result.get('rating')
        self.place.opening_hours_text = result.get('opening_hours', {}).get('weekday_text', [])
        self.place.opening_hours = result.get('opening_hours', {}).get('periods', [])
        return self.place

    def parse_kg_data(self, kg_json):
        '''Parses information from Google knowledge graph. 
        Retrieves the following:
        Category (via method get_category)
        Tags (set object)
        Detailed Description
        '''
        kg_data = kg_json.get('itemListElement')
        if kg_data:
            results = kg_data[0]['result']
            if results['name'] == self.place.name:
                self.place.category = self.get_category(results.get('description'))
                self.place.append_tags(results.get('@type', []))
                self.place.descrip_long = results.get('detailedDescription', {}).get('articleBody')
            else:
                print(f'KG Verification error, getting summary from wikipedia instead')
                self.place.descrip_long = self.get_summary(self.place.name)
        else:
            print(f'No KG results, trying wikipedia instead')
            self.place.descrip_long = self.get_summary(self.place.name)
        return self.place

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
    
    def get_summary(self, name):
        try:
            wiki = wikipedia.WikipediaPage(name)
        except wikipedia.DisambiguationError as e:
            for option in e.options:
                if self.place.city in option.lower():
                    wiki = wikipedia.page(option)
                    break
            if not wiki:
                wiki = wikipedia.page(e.options[0])
        except:
            self.place.descrip_long = ''
            return
        sentences = sent_tokenize(wiki.summary)[:2]
        summary = re.sub(self.parenthesis_content, '', ' '.join(sentences))
        return summary
    
    def categorize(self):
        predefined_categories = [
            'Museum', 'Zoo', 'Aquarium', 'Theatre', 'Theme Park', \
            'Market', 'District', 'Tower', 'Bridge', 'Public Art', \
            'Mountain', 'Park', 'Garden', 'Island', 'Lake', 'Beach', \
            'Historical Landmark', 'Religious Landmark', 'Monument', \
            'Novelty']
        

class SearchError(Exception):
    pass

class GoogleHotelDetailer(GooglePlacesDetailer):
    def __init__(self):
        pass

class GoogleEatsDetailer(GooglePlacesDetailer):
    def __init__(self):
        pass




if __name__ == '__main__':
    url = 'https://www.google.com/travel/things-to-do/see-all?g2lb=2502548%2C4258168%2C4260007%2C4270442%2C4274032%2C4291318%2C4305595%2C4306835%2C4317915%2C4322822%2C4326765%2C4328159%2C4329288%2C4366684%2C4367953%2C4373849%2C4385383%2C4386665%2C4387290%2C4388508%2C4270859%2C4284970%2C4291517%2C4316256%2C4356900&hl=en&gl=us&un=1&otf=1&dest_mid=%2Fm%2F07dfk&dest_state_type=sattd&tcfs=EgoKCC9tLzA3ZGZr&sa=X&ved=0ahUKEwiBhpS79NzpAhUTK30KHcTgChsQx2gIGA#ttdm=35.674835_139.763908_11&ttdmf=%252Fm%252F07thkr'
    city = 'Tokyo'
    country = 'Japan'

    #url = 'https://www.google.com/travel/things-to-do?g2lb=2502548%2C4258168%2C4270442%2C4305595%2C4306835%2C4317915%2C4319922%2C4322823%2C4328159%2C4367953%2C4371334%2C4381263%2C4384467%2C4393966%2C4401769%2C4402623%2C4403882%2C4412670%2C4270859%2C4284970%2C4291517%2C4412693&hl=en&gl=us&un=1&otf=1&dest_mid=%2Fm%2F09d4_&dest_state_type=main&dest_src=ts&sa=X&ved=2ahUKEwiWteeav-7qAhURip4KHQotDGsQuL0BMAF6BAgEECA#ttdm=34.989201_135.732489_12'
    #city = 'Kyoto'
    #country = 'Japan'

    
    finder = GooglePlacesFinder(city, country)
    finder.run(url)
    finder.save_df()
    finder.save_excel()