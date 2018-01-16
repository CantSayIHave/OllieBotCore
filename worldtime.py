# worldtime module by CantSayIHave
# Created 2018/01/12
#
# Fetch time and date from a location
# Uses Google Geocoding API and Google Time Zone API

import aiohttp
import time
from datetime import datetime


API_GEOCODE = 'https://maps.googleapis.com/maps/api/geocode/json?'
API_TIMEZONE = 'https://maps.googleapis.com/maps/api/timezone/json?'

allowed_chars = [',', '%', '+', '-']


class Location:
    def __init__(self, address: str, lat: int = None, long: int = None):
        self.address = address
        self.latitude = lat
        self.longitude = long


class Time:
    def __init__(self, time: datetime, timezone_id: str, timezone_name: str):
        self.time = time
        self.timezone_id = timezone_id
        self.timezone_name = timezone_name


class WorldTime:
    def __init__(self, key: str):
        self.key = key

    async def get_location(self, query: str) -> Location:
        args = {'address': self.query_encode(query),
                'key': self.key}

        url = API_GEOCODE + self.param_encode(args)

        search = await self.api_get(url)

        if search:
            try:
                result = search['results'][0]
                location = Location(address=result['formatted_address'],
                                    lat=result['geometry']['location']['lat'],
                                    long=result['geometry']['location']['lng'])
                return location
            except KeyError:
                print('WorldTime Location Key Error')
                raise
        else:
            return search

    async def get_time(self, location: Location) -> Time:
        unix_now = int(time.time())

        args = {'location': '{},{}'.format(location.latitude, location.longitude),
                'timestamp': unix_now,
                'key': self.key}

        url = API_TIMEZONE + self.param_encode(args)

        search = await self.api_get(url)

        if search:
            try:
                location_time = unix_now + search['rawOffset'] + search['dstOffset']
                return Time(time=datetime.fromtimestamp(location_time),
                            timezone_id=search['timeZoneId'],
                            timezone_name=search['timeZoneName'])
            except KeyError:
                print('WorldTime Time Key Error')
                raise
        else:
            return search


    @staticmethod
    async def api_get(url: str) -> dict:
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    j = await resp.json()
                    if j['status'] == 'OK':
                        return j
                    elif j['status'] == 'ZERO_RESULTS':
                        return None
                return False

    @staticmethod
    def query_encode(text: str) -> str:
        text = ' '.join(text.split())
        text = text.replace(' ', '+')
        for c in text:
            if c not in allowed_chars and not c.isalnum():
                text = text.replace(c, '%' + hex(ord(c))[2:])
        return text

    @staticmethod
    def param_encode(options: dict) -> str:
        out = ''
        for k, v in options.items():
            out += '{}={}&'.format(k, v)
        out = out[:-1]
        return out
