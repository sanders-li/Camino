import json
from requests_html import HTMLSession
from contextlib import suppress
import os

class WebRequestHandler():
    def __init__(self):
        self.session = HTMLSession()
        basepath = os.path.dirname(__file__)
        keypath = os.path.abspath(os.path.join(basepath, 'keys.json'))
        with open(keypath, 'r') as f:
            self.api_keys = json.loads(f.read())

    def __enter__(self):
        return self
    
    def __exit__(self):
        self.session.close()

    def call_api(self, api_url, params):
        #r = self.fetch_url_data(api_url, params=params)
        r = self.fetch_url_data(api_url + '?' + params)
        result = json.loads(r.text)
        if self.response_checker(result):
            return result

    def response_checker(self, result):
        raise NotImplementedError

    def fetch_url_data(self, url):
        print(f'Accessing: {url}')
        r = self.session.get(url)
        if r.status_code == 200:
            return r

class GoogleApiHandler(WebRequestHandler):
    def __init__(self):
        super().__init__()
        
    def response_checker(self, result):
        '''Translates Google Place API specific text response to a dictionary object'''
        status_error_codes = ["ZERO_RESULTS", "OVER_QUERY_LIMIT", "REQUEST_DENIED", "INVALID_REQUEST", "UNKNOWN_ERROR"]
        with suppress(KeyError):
            if result['error'] or result['status'] in status_error_codes:
                raise IOError
        return True