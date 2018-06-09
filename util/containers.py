
class BlockItem:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.channel = kwargs.get('channel', 'all')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "BlockItem:[n={}, ch={}]".format(self.name, self.channel)


class Feed:
    def __init__(self, **kwargs):
        self.uid = kwargs.get('uid', '')
        self.channel_id = kwargs.get('channel_id', '')
        self.last_id = kwargs.get('last_id', '')
        self.last_time = kwargs.get('last_time', '')
        self.type = kwargs.get('type', '')
        self.title = kwargs.get('title', '')
        self.user = kwargs.get('user', '')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Feed:[uid={}, chid={}, lid={}, lt={}, tp={}, ti={}, u={}]".format(self.uid,
                                                                                  self.channel_id,
                                                                                  self.last_id,
                                                                                  self.last_time,
                                                                                  self.type,
                                                                                  self.title,
                                                                                  self.user)


class MutedMember:
    def __init__(self, **kwargs):
        self.member = kwargs.get('member', None)
        self.timer = kwargs.get('timer', 60)
        self.audio_mute = kwargs.get('audio_mute', True)
        self.text_mute = kwargs.get('text_mute', True)
        self.bot = kwargs.get('bot', None)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "MutedMember:[m={}, t={}, am={}, tm={}, b={}]".format(self.member,
                                                                     self.timer,
                                                                     self.audio_mute,
                                                                     self.text_mute,
                                                                     self.bot)


class DeleteMessage:
    def __init__(self, **kwargs):
        self.message = kwargs.get('message', None)
        self.timer = kwargs.get('timer', 10)
        self.bot = kwargs.get('bot', None)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "DeleteMessage:[m={}, t={}, b={}]".format(self.message,
                                                     self.timer,
                                                     self.bot)


class ProxyMessage:
    def __init__(self, **kwargs):
        self.channel = kwargs.get('channel', None)
        self.content = kwargs.get('content', '')
        self.embed = kwargs.get('embed', None)
        self.bot = kwargs.get('bot', None)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "ProxyMessage:[ch={}, cn={}, e={}, b={}]".format(self.channel,
                                                             self.content,
                                                             self.embed,
                                                             self.bot)


class TimedFuture:
    def __init__(self, **kwargs):
        self.coro = kwargs.get('coro', None)
        self.timer = kwargs.get('timer', 0)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "TimedFuture:[c={}, t={}]".format(self.coro,
                                                 self.timer)


class EmbedField:
    def __init__(self, name: str = chr(0x200B), value: str = chr(0x200B), inline=True):
        self.name = name
        self.value = value
        self.inline = inline

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "BlockItem:[n={}, v={}, i={}]".format(self.name,
                                                     self.value,
                                                     self.inline)


class CommandContext:
    def __init__(self, content: str, bot):
        self.content = content
        self.is_command = (content.find(bot.command_prefix) == 0)
        self.command = content[:content.find(' ')]
        if self.is_command:
            self.command = self.command[len(bot.command_prefix):]


class HelpForm:
    def __init__(self, content: str):
        self.content = content
        self.details = {}

    def __str__(self):
        return self.content

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return 1 + len(self.content)

    def add_detail(self, keyword: str, content: str):
        self.details[keyword] = content

    def detail(self, keyword):
        if keyword in self.details:
            return self.details[keyword]

    def format(self, *args, **kwargs):
        return self.content.format(*args, **kwargs)
