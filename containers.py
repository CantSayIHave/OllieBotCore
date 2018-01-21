
class BlockItem:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.channel = kwargs.get('channel', 'all')


class Feed:
    def __init__(self, **kwargs):
        self.uid = kwargs.get('uid', '')
        self.channel_id = kwargs.get('channel', '')
        self.last_id = kwargs.get('last_id', '')
        self.last_time = kwargs.get('last_time', '')
        self.type = kwargs.get('type', '')
        self.title = kwargs.get('title', '')
        self.user = kwargs.get('user', '')


class MutedMember:
    def __init__(self, **kwargs):
        self.member = kwargs.get('member', None)
        self.timer = kwargs.get('timer', 60)
        self.audio_mute = kwargs.get('audio_mute', True)
        self.text_mute = kwargs.get('text_mute', True)
        self.bot = kwargs.get('bot', None)


class DeleteMessage:
    def __init__(self, **kwargs):
        self.message = kwargs.get('message', None)
        self.timer = kwargs.get('timer', 10)
        self.bot = kwargs.get('bot', None)


class ProxyMessage:
    def __init__(self, **kwargs):
        self.channel = kwargs.get('channel', None)
        self.content = kwargs.get('content', '')
        self.embed = kwargs.get('embed', None)
        self.bot = kwargs.get('bot', None)