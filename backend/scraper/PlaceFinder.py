from WebRequestHandler import WebRequestHandler
from bs4 import BeautifulSoup
#import lxml
from collections import defaultdict, namedtuple

from Place import Sight, Hotel, Eatery

#Finder   
class GooglePlacesFinder(WebRequestHandler):
    def __init__(self, city, country):
        super().__init__()
        self.city = city.lower()
        self.country = country.lower()
    
    def things_to_do_scrape(self, url):
        '''Given URL of Google Travel Sights, scrapes HTML data for sights.
        Returns list of sights to be parsed for information
        '''
        r = self.fetch_url_data(url)
        xpath = '//*[@id="yDmH0d"]/c-wiz[2]/div/div[2]/div/c-wiz/div/div/div[1]/div[2]/c-wiz/div/div[1]/div/div/div'
        scraped_sights = defaultdict()
        for item in r.html.xpath(xpath):
            name = item.find('.skFvHc.YmWhbc', first=True).text
            descrip = item.find('.nFoFM', first=True).text
            if name in scraped_sights:
                raise KeyError
            else:
                scraped_sights[name] = Sight({'name': name, 'summary': descrip, 'city': self.city, 'country': self.country})
        return scraped_sights