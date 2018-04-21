# response.py by Sierra
# Response class for managing bot responses to keywords and commands
import random
import discord

# Class Response:
#  |Attributes|
#   - name: name for identification
#   - content: # actual content - interpreted string or image link
#   - id: used instead of name for activation if present
#   - is_command: whether response needs a prefix to activate
#   - is_image: True for image link, False for interpreted string
#   - is_quote: whether command is quote - content + @ca + author
#   - high_permissions: whether response requires high permissions
#   - spam_timer: set to None to delete
#   - timer: holds actual time value
#   - search_type: 'explicit' or  'contains' for how to find response
#   - delete: timer to delete response
#
#  |Methods|
#   - add_author: append author suffix and author to content


class Response:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', "")
        self.content = kwargs.get('content', "")
        self.id = kwargs.get('id', None)
        self.is_image = kwargs.get('is_image', False)
        self.high_permissions = kwargs.get('high_permissions', False)
        self.is_command = kwargs.get('is_command', True)
        self.spam_timer = kwargs.get('spam_timer', 1)
        self.timer = kwargs.get('timer', 0)
        self.is_quote = kwargs.get('is_quote', False)
        self.search_type = kwargs.get('search_type', 'explicit')
        self.delete = kwargs.get('delete', 10)
        self.mentions = kwargs.get('mentions', [])  # list of strings (id's)

        if self.is_num(self.delete):
            self.delete = int(self.delete)

        if self.is_num(self.spam_timer):
            self.spam_timer = int(self.spam_timer)

        if self.search_type != 'explicit' and self.search_type != 'contains' and self.search_type != 'exact':
            self.search_type = 'contains'

        if ' ' in self.name and self.search_type != 'exact':
            self.search_type = 'contains'

        self.name = self.name.replace('+', ' ')

        if self.is_image:
            self.is_quote = False

        if self.is_quote:
            self.is_image = False

        if self.is_quote:
            self.add_author(kwargs.get('author', ''))

    def edit(self, **kwargs):
        self.name = kwargs.get('name', self.name)
        self.content = kwargs.get('content', self.content)
        self.id = kwargs.get('id', self.id)
        self.is_image = kwargs.get('is_image', self.is_image)
        self.high_permissions = kwargs.get('high_permissions', self.high_permissions)
        self.is_command = kwargs.get('is_command', self.is_command)
        self.spam_timer = kwargs.get('spam_timer', self.spam_timer)
        self.is_quote = kwargs.get('is_quote', self.is_quote)
        self.search_type = kwargs.get('search_type', self.search_type)
        self.delete = kwargs.get('delete', self.delete)

        if self.is_num(self.delete):
            self.delete = int(self.delete)

        if self.is_num(self.spam_timer):
            self.spam_timer = int(self.spam_timer)

        if self.search_type != 'explicit' and self.search_type != 'contains' and self.search_type != 'exact':
            self.search_type = 'contains'

        self.name = self.name.replace('+', ' ')

        if self.is_image:
            self.is_quote = False

        if self.is_quote:
            self.is_image = False

        if self.is_quote:
            self.add_author(kwargs.get('author', ''))

    def add_author(self, author: str):
        if author:
            self.content += '@ca' + author

    @staticmethod
    def is_num(thing):
        try:
            num = int(thing)
            return num
        except Exception:
            return None


# Class ResponseLibrary:
#  |Attributes|
#   - responses: list of Response objects
#   - response_ids: names and ids of response objects for faster searching
#   - g_spam_timer: default global spam timer
#
#  |Methods|
#   - add: add a response to `responses`
#   - edit: edit a response
#   - remove: remove a response
#   - get: gets a response by name/id
#   - has: checks for membership of a name/id
#   - get_occurrence: retrieves a response from a message by occurrence anywhere
#   - get_explicit: retrieves a response from a message by splitting and searching
#   - get_processed: returns processed embed or string of a response given context
#   - dec_spam_timers: decrease all spam timers by a value
#   - interpret_response: interprets and processes tags in response content
#   - fix_album_full: fixes albums by breaking down and rebuilding
#   - fix_album: fixes albums by replacing known errors


class ResponseLibrary:
    def __init__(self, spam_timer: int):
        self.responses = []  #: :type: list of Response
        self.response_ids = []
        self.g_spam_timer = spam_timer

    def add(self, resp: Response):
        self.responses.append(resp)
        self.response_ids.append(resp.name)
        if resp.id:
            self.response_ids.append(resp.id)

        if resp.is_image:
            resp.content = self.fix_album(resp.content)

        return resp

    def edit(self, resp: Response, changes: dict):
        if 'name' in changes:
            try:
                self.response_ids.remove(resp.name)
            except (ValueError, AttributeError):
                pass
            self.response_ids.append(changes['name'])
        if 'id' in changes:
            try:
                self.response_ids.remove(resp.id)
            except (ValueError, AttributeError):
                pass
            self.response_ids.append(changes['id'])

        resp.edit(**changes)

        if resp.id:
            self.response_ids.append(resp.id)

        if resp.is_image:
            resp.content = self.fix_album(resp.content)

        return resp

    def remove(self, query: str):
        to_rem = self.get(query)
        if to_rem:
            self.response_ids.remove(to_rem.name)
            if to_rem.id:
                self.response_ids.remove(to_rem.id)
            self.responses.remove(to_rem)
            return True
        return False

    def get(self, query: str, by_name=False) -> Response:
        for r in self.responses:  # type: Response
            if r.id and not by_name:
                if query == r.id:
                    return r
            if query == r.name:
                return r
        return None

    # Use to reduce search time for query membership
    def has(self, query: str):
        return query in self.response_ids

    # use to reduce search time for keyword membership in message
    def get_occurrence(self, text: str):
        for r in self.responses:  # type: Response
            if not r.is_command and r.search_type == 'contains':
                if r.id:
                    if r.id in text:
                        print('found ' + r.id)
                        return r
                if r.name in text:
                    print('found ' + r.name)
                    return r
        return None

    def get_explicit(self, text: str):
        pieces = text.split(' ')
        for word in pieces:
            r = self.get(word)
            if r:
                if r.search_type == 'explicit' and not r.is_command:
                    return r
        return None

    def get_exact(self, content: str):
        if len(content) > 30:
            return None
        r = self.get(content)
        if r:
            if r.search_type == 'exact':
                return r
            return None

    def get_processed(self,
                      response: Response,
                      msg: discord.Message = None,
                      args: list = None,
                      has_high_perm: bool = False,
                      first_arg: bool = False):

        if not response:
            return None

        # command (first arg activation) check
        if response.is_command and not first_arg:
            return None

        # high permission check
        if response.high_permissions and not has_high_perm:
            return None

        # check / set spam timer if applicable
        if not has_high_perm:
            if response.spam_timer is not None:
                if response.timer > 0:
                    return None
                response.timer = int(response.spam_timer) * 60

        # process image
        if response.is_image:
            base = response.content
            if base.find(' @r ') != -1:
                base = random.choice(base.split(' @r '))
            if base.find(' @m ') != -1:
                return base.replace(' @m ', '\n')
            em = discord.Embed(color=random.randint(0, 0xffffff))
            em.set_image(url=base.replace(' ', '').replace('%22', ''))
            return em

        # interpret in-line arguments
        text = self.interpret_response(response.content, msg, args)

        # embed single images
        if 'http' in text and text.endswith(('jpg', 'png', 'gif', 'jpglarge')):
            text_parts = text.split('http')
            url = 'http' + text_parts[1]
            em = discord.Embed(title=chr(0x200B), description=text_parts[0], color=random.randint(0, 0xffffff))
            em.set_image(url=url.replace(' ', '').replace('%22', ''))
            return em

        if response.is_quote:
            author = None
            if text.find('@ca') != -1:
                author = text[text.find('@ca')+3:]
                text = text[:text.find('@ca')]

            if author:
                return '"{}" - {}'.format(text, author)
            else:
                return '"{}"'.format(text)
        else:
            return text

    def dec_spam_timers(self, value: int):
        for r in self.responses:
            if r.spam_timer:
                if r.timer > 0:
                    r.timer -= value

    def interpret_response(self, text: str, msg: discord.Message = None, args: list = None) -> str:
        if '@ru' in text and args:
            text = text.replace('@u', '@a')
        text = text.replace('@ru', '')

        if '@ra' in text and not args:
            text = text.replace('@a ', '@u ')
        text = text.replace('@ra', '')

        use_name = False
        if '@rn' in text:
            use_name = True
        text = text.replace('@rn', '')
        print('found rn')

        piece1 = None
        if ' @and ' in text:
            pieces = text.split(' @and ')
            if use_name:
                piece1 = self.interpret_response(text=pieces[0] + '@rn', msg=msg, args=args)
            else:
                piece1 = self.interpret_response(text=pieces[0].replace(' @and ', ''), msg=msg, args=args)
            text = pieces[1]

        if text.find(' @r ') != -1:
            r_keys = text.split(' @r ')
            text = random.choice(r_keys)
        if text.find('@u') != -1:
            if not msg:
                raise ValueError('Must pass message to use @u')

            if not use_name:
                text = text.replace('@u', msg.author.mention)
            else:
                text = text.replace('@u', '**{}**'.format(msg.author.display_name))
        if text.find('@a') != -1:
            if not args:
                text = text.replace('@a', '')
            else:
                index = 0
                while '@a' in text:
                    arg = str(args[index])

                    if msg.mentions and use_name:
                        msg_mentions = [x for x in msg.mentions if x.mention == arg]
                        if msg_mentions:
                            text = text.replace('@a', '**{}**'.format(msg_mentions[0].display_name), 1)
                        else:
                            text = text.replace('@a', str(arg), 1)
                    else:
                        text = text.replace('@a', str(arg), 1)
                    index += 1
                    if index >= len(args):
                        break
                text = text.replace('@a', '')
        if text.find('```') == -1:
            text = text.replace('`', '')
        while '%d' in text:
            text = text.replace('%d', str(random.randint(0, 9)), 1)
        text = text.replace(' @m ', '\n')
        if piece1:
            return '{} {}'.format(piece1, text)
        else:
            return text

    # fixes albums by breaking down all selections and looking for empty strings
    # O(n) <- probably
    @staticmethod
    def full_fix_album(text: str) -> str:
        rkeys = text.split(' @r ')
        nrkeys = []
        for rk in rkeys:
            mkeys = rk.split(' @m ')
            for mk in mkeys:
                if len(mk) < 1:
                    mkeys.remove(mk)
            nrk = ' @m '.join(mkeys)
            if len(nrk) > 0:
                nrkeys.append(nrk)
        return ' @r '.join(nrkeys)

    # fixes albums by replacing known errors
    # O(i don't know) (probably faster?)
    @staticmethod
    def fix_album(text: str) -> str:
        text = text.replace('@u', '')
        text = text.replace('@a', '')
        text = text.replace('@ru', '')
        text = text.replace('@ca', '')
        text = text.replace(' @m  @m ', ' @m ')
        text = text.replace(' @r  @m ', ' @r ')
        text = text.replace(' @m  @r ', ' @r ')
        text = text.replace(' @r  @r ', ' @r ')
        while text[:4] == ' @r ' or text[:4] == ' @m ':
            text = text[4:]
        while text[-4:] == ' @r ' or text[-4:] == ' @m ':
            text = text[:-4]
        return text


