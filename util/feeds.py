from datetime import datetime
from abc import ABCMeta, abstractmethod
import random


class RssFeed(metaclass=ABCMeta):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '0')
        self.discord_channel_id = kwargs.get('discord_channel_id', '0')

        self.first_time = False

        if not self.id:  # datetime + random ensures (good chance of) randomness
            self.id = datetime.now().strftime('%y%m%d%H%M%S') + str(random.randint(1000, 10000))

    def update(self, feed):
        return

    def __repr__(self):
        return self.__str__()

    @abstractmethod
    def as_dict(self):
        return {'id': self.id, 'discord_channel_id': self.discord_channel_id}

    @abstractmethod
    def brief(self):
        """Provides ID and last resource ID in a dict"""
        pass

    @abstractmethod
    def name(self):
        """Provides a title for standardized searching"""
        pass

    @abstractmethod
    def channel_id(self):
        """Provides whatever qualifies as the channel id"""
        pass

    @abstractmethod
    def string_type(self):
        """Provides type as simple string"""
        pass

    """Soft abstract: `channel_id` property"""


class TwitterFeed(RssFeed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.handle = kwargs.get('handle', '')
        self.last_tweet_id = kwargs.get('last_tweet_id', '')

    def __str__(self):
        return 'TwitterFeed:[h={}, lid={}, id={}]'.format(self.handle,
                                                          self.last_tweet_id,
                                                          self.id)

    def update(self, feed):
        self.handle = feed.handle
        self.last_tweet_id = feed.last_tweet_id

    def as_dict(self):
        attrs = super().as_dict()
        attrs.update({'type': 'twitter',
                      'handle': self.handle,
                      'last_tweet_id': self.last_tweet_id})
        return attrs

    def brief(self):
        return {'id': str(self.id), 'last_feed_id': str(self.last_tweet_id)}

    @property
    def name(self):
        return self.handle

    @property
    def channel_id(self):
        return self.handle

    def string_type(self):
        return 'twitter'


class TwitchFeed(RssFeed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._channel_id = kwargs.get('channel_id', None)
        self.last_stream_id = kwargs.get('last_stream_id', '')
        self.title = kwargs.get('title', '')
        self.user_id = kwargs.get('user_id', '')
        self.last_time = kwargs.get('last_time', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

    def __str__(self):
        return 'TwitchFeed:[chid={}, lid={}, ti={}, uid={}, id={}]'.format(self.channel_id,
                                                                           self.last_stream_id,
                                                                           self.title,
                                                                           self.user_id,
                                                                           self.id)

    def update(self, feed):
        self._channel_id = feed.channel_id
        self.last_stream_id = feed.last_stream_id
        self.title = feed.title
        self.user_id = feed.user_id
        self.last_time = feed.last_time

    def as_dict(self):
        attrs = super().as_dict()
        attrs.update({'type': 'twitch',
                      'channel_id': self.channel_id,
                      'last_stream_id': self.last_stream_id,
                      'title': self.title,
                      'last_time': self.last_time})
        return attrs

    def brief(self):
        return {'id': str(self.id), 'last_feed_id': str(self.last_stream_id)}

    @property
    def name(self):
        return self.title

    @property
    def channel_id(self):
        return self._channel_id

    def string_type(self):
        return 'twitch'


class YouTubeFeed(RssFeed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._channel_id = kwargs.get('channel_id', '')
        self.title = kwargs.get('title', '')
        self.last_video_id = kwargs.get('last_video_id', '')
        self.last_time = kwargs.get('last_time', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

    def __str__(self):
        return 'YouTubeFeed:[chid={}, ti={}, lid={}, id={}]'.format(self.channel_id,
                                                                    self.title,
                                                                    self.last_video_id,
                                                                    self.id)
    
    def update(self, feed):
        self._channel_id = feed.channel_id
        self.title = feed.title
        self.last_video_id = feed.last_video_id
        self.last_time = feed.last_time

    def as_dict(self):
        attrs = super().as_dict()
        attrs.update({'type': 'YouTubeFeed',
                      'channel_id': self.channel_id,
                      'title': self.title,
                      'last_video_id': self.last_video_id,
                      'last_time': self.last_time})
        return attrs

    def brief(self):
        return {'id': str(self.id), 'last_feed_id': str(self.last_video_id)}

    @property
    def name(self):
        return self.title

    @property
    def channel_id(self):
        return self._channel_id

    def string_type(self):
        return 'youtube'


def build_feed(raw: dict) -> RssFeed:
    f_type = raw['type']
    if f_type in ['twitter', 'TwitterFeed']:
        return TwitterFeed(**raw)
    elif f_type in ['twitch', 'TwitchFeed']:
        return TwitchFeed(**raw)
    elif f_type in ['youtube', 'YouTubeFeed']:
        return YouTubeFeed(**raw)
    else:
        raise ValueError('Unsupported feed type.')

