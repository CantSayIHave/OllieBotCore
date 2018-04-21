import aiohttp


class OllieBotAPI:
    """Accesses features of bot.olliebot.cc

    """

    API_URL = "https://bot.olliebot.cc/"

    def __init__(self, token):
        self.token = token

    async def get_eight_ball(self, fn: str = None) -> str:
        """Returns a random eight ball image

        Parameters
        ----------
        fn : str
            a specific filename to retrieve. returns random if 'None'

        Returns
        -------
        str
            url of file

        """

        if fn:
            url = self._build_url('eb', img=fn)
        else:
            url = self._build_url('eb')

        print('url:{}'.format(url))

        resp = await self._get_json(url)

        if resp:
            return resp['url']

    def _build_url(self, endpoint: str, **args) -> str:
        """Constructs a request url for any api endpoint

        Follows the format https://{domain}/{endpoint}?{arg}={value}&{arg2}={value}

        Sample request:  https://bot.olliebot.cc/eb?img=no.png

        Parameters
        ----------
        endpoint : str
            the id of the api endpoint to access
        args : dict
            arguments to be written in `arg1=val&arg2=val` notation
        """

        if 'token' not in args:
            args['token'] = self.token
        return "{}{}?{}".format(self.API_URL, endpoint, '&'.join(["{}={}".format(x, args[x]) for x in args]))

    @staticmethod
    async def _get_json(page: str) -> dict:
        with aiohttp.ClientSession() as session:
            async with session.get(page) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    return d

