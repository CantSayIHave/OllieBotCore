from datetime import datetime

import storage_manager_v2 as storage
import discord
from discordbot import DiscordBot
from util import global_util
from util.feeds import *


class Feeds:
    rss_feed_types = ['twitter', 'twitch', 'youtube']

    def __init__(self, bot: DiscordBot):
        self.bot = bot

        @self.bot.group(pass_context=True)
        async def rss(ctx):
            pass

        # Creates an rss feed in [User | Channel ID | Last Tweet ID] format
        @rss.command(pass_context=True)
        @self.bot.test_high_perm
        async def add(server, ctx, platform: str, user: str):
            if platform.lower() not in self.rss_feed_types:
                await self.bot.say('Sorry, {} is not a valid feed type.\n'
                                   'Supported feeds include Twitch, Twitter and YouTube'
                                   ''.format(platform))
                return

            platform = platform.lower()

            if platform == 'twitter' and user[0] == '@':
                user = user[1:]  # takes @ off a username

            feed_channel = ctx.message.channel

            if platform == 'twitter':
                if server.get_feed(feed_channel, type=platform, name=user):  # if rss exists, cancel
                    await self.bot.say('User `@{}` already has a Twitter feed on this channel'.format(user))
                    return

                try:
                    await server.add_twitter_feed(feed_channel, handle=user)
                except Exception as e:
                    await self.bot.say('No user `@{}` exists!\nExcept {}'.format(user, e))
                    return

                storage.write_feeds(server)
                await self.bot.say('Added Twitter feed for `@{}` to {}'.format(user, feed_channel.mention))
                global_util.rss_timer = 70

            elif platform == 'twitch':
                twitch_channel = await global_util.twitch.get_channel_from_name(user)
                if not twitch_channel:
                    await self.bot.say('Twitch user `{}` does not exist'.format(user))
                    return

                if server.get_feed(feed_channel, type=platform, channel_id=twitch_channel['_id']):
                    await self.bot.say('User `{}` already has a Twitch feed on this channel'
                                       ''.format(twitch_channel['display_name']))
                    return

                try:
                    await server.add_twitch_feed(feed_channel, username=user)
                except:
                    await self.bot.say('Something went wrong, couldn\'t add feed :(')
                    return

                storage.write_feeds(server)
                await self.bot.say('Added Twitch feed for `{}` to channel {}'.format(twitch_channel['display_name'],
                                                                                     feed_channel.mention))
                global_util.rss_timer = 70

            elif platform == 'youtube':

                """Channel links take forms:
                www.youtube.com/user/someusername
                www.youtube.com/channel/somechannelid
                """

                yt_channel = None

                if user.startswith('http'):
                    url = user
                    if 'user/' in url:
                        username = url.split('user/')[1]
                        yt_channel = await global_util.yt.get_channel_by_name(username)

                    elif 'channel/' in url:
                        channel_id = url.split('channel/')[1]
                        yt_channel = await global_util.yt.get_channel_by_id(channel_id)

                    else:
                        await self.bot.say('This link is invalid, please provide a valid channel link 🔗')
                        return
                else:
                    yt_channel = await global_util.yt.get_channel_by_name(user)

                if not yt_channel:
                    await self.bot.say('Youtube user `{}` does not exist'.format(user))
                    return

                channel_id = yt_channel['id']

                if server.get_feed(feed_channel, type=platform, channel_id=yt_channel['id']):  # if rss exists, cancel
                    await self.bot.say('User `{}` already has a YouTube feed on this channel'
                                       ''.format(yt_channel['snippet']['title']))
                    return

                try:
                    await server.add_youtube_feed(feed_channel, channel_id=channel_id)
                except:
                    await self.bot.say('Something went wrong, couldn\'t add feed :(')
                    return

                storage.write_feeds(server)
                await self.bot.say('Added YouTube feed for `{}` to channel {}'.format(yt_channel['snippet']['title'],
                                                                                      feed_channel.mention))
                global_util.rss_timer = 70

        @rss.command(pass_context=True)
        @self.bot.test_high_perm
        async def remove(server, ctx, platform: str, user: str):

            if platform.lower() not in self.rss_feed_types:
                await self.bot.say('Sorry, {} is not a valid feed type.\n'
                                   'Supported feeds include Twitch, Twitter and YouTube'.format(platform))
                return

            if platform == 'twitter' and user[0] == '@':
                user = user[1:]  # takes @ off a handle

            platform = platform.lower()

            feed_channel = ctx.message.channel

            if platform == 'twitter':
                feed = server.get_feed(feed_channel, name=user, type=platform, search_lower=True)

                if feed:
                    deleted = await server.remove_feed(feed)  # type: TwitterFeed
                    storage.write_feeds(server)
                    await self.bot.say('Removed Twitter feed for `@{}` from {}'.format(deleted.handle,
                                                                                       feed_channel.mention))
                else:
                    await self.bot.say('No Twitter feed for `@{}` exists on this channel'.format(user))

            elif platform == 'twitch':
                feed = server.get_feed(feed_channel, name=user, type=platform, search_lower=True)

                if feed:
                    deleted = await server.remove_feed(feed)  # type: TwitchFeed
                    storage.write_feeds(server)
                    await self.bot.say('Removed Twitch feed for `{}` from {}'.format(deleted.title,
                                                                                     feed_channel.mention))
                else:
                    await self.bot.say('No Twitch feed for `{}` exists on this channel'.format(user))

            elif platform == 'youtube':
                feed = server.get_feed(feed_channel, name=user, type=platform, search_lower=True)

                if feed:
                    deleted = await server.remove_feed(feed)
                    storage.write_feeds(server)
                    await self.bot.say('Removed YouTube feed for `{}` from {}'.format(deleted.title,
                                                                                      feed_channel.mention))
                else:
                    await self.bot.say('No YouTube feed for `{}` exists on this channel'.format(user))

        @rss.command(pass_context=True)
        async def listall(ctx, arg=None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if in_server.feeds:
                out_str = ""

                if arg == 'debug':
                    for r in in_server.feeds:  # type: Feed
                        if isinstance(r, TwitterFeed):
                            out_str += 'User `@{}` has a Twitter feed on <#{}>, ' \
                                       'fid={}, lid={}\n'.format(r.handle, r.discord_channel_id, r.id, r.last_tweet_id)
                        elif isinstance(r, YouTubeFeed):
                            out_str += 'User `{}` has a YouTube feed on <#{}>, ' \
                                       'fid={}, lid={}\n'.format(r.title, r.discord_channel_id, r.id, r.last_video_id)
                        elif isinstance(r, TwitchFeed):
                            out_str += 'User `{}` has a Twitch feed on <#{}>, ' \
                                       'fid={}, lid={}\n'.format(r.title, r.discord_channel_id, r.id, r.last_stream_id)
                else:
                    for r in in_server.feeds:  # type: Feed
                        if isinstance(r, TwitterFeed):
                            out_str += 'User `@{}` has a Twitter feed on <#{}>\n'.format(r.handle, r.discord_channel_id)
                        elif isinstance(r, YouTubeFeed):
                            out_str += 'User `{}` has a YouTube feed on <#{}>\n'.format(r.title, r.discord_channel_id)
                        elif isinstance(r, TwitchFeed):
                            out_str += 'User `{}` has a Twitch feed on <#{}>\n'.format(r.title, r.discord_channel_id)

                await self.bot.say(out_str)

        @rss.command(pass_context=True)
        async def force(ctx, feed_type: str, user: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.check_admin(ctx.message.author):
                return

            for r in in_server.feeds:
                if (feed_type.lower() == r.type) and (user == r.title):  # WHAT THE HELL IS ALL THIS
                    r.last_id = 'none'
                    last_time = datetime.strptime(r.last_time[:r.last_time.find('.')], '%Y-%m-%dT%H:%M:%S')
                    last_time = last_time.replace(year=last_time.year - 1)
                    r.last_time = last_time.strftime('%Y-%m-%dT%H:%M:%S') + '.'  # WHAT WAS I THINKING
                    global_util.rss_timer = 70

        @rss.command(pass_context=True)
        async def clear(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            await self.bot.say('Clearing all rss.')
            in_server.feeds = []
            storage.write_feeds(in_server)

        @rss.command(pass_context=True)
        @self.bot.test_high_perm
        async def setid(server, ctx, feed_id, new_content_id):
            feed = server.get_feed(id=feed_id)

            if not feed:
                await self.bot.say('Feed not found.')
                return

            if isinstance(feed, TwitterFeed):
                feed.last_tweet_id = int(new_content_id)
            elif isinstance(feed, TwitchFeed):
                feed.last_stream_id = new_content_id
            elif isinstance(feed, YouTubeFeed):
                feed.last_video_id = new_content_id

            await self.bot.say('Updated.')

            storage.write_feeds(server)

            global_util.rss_timer = 60

        @rss.command(pass_context=True)
        async def help(ctx, arg: str = None):

            if not self.bot.has_high_permissions(ctx.message.author):
                return

            if arg == 'users':
                await self.bot.send_message(ctx.message.author,
                                            "For Twitter, use the user's twitter handle, like "
                                            "`@Shoe0nHead`\n "
                                            "For Twitch, use the username found in the url format "
                                            "`www.twitch.tv/[username]`\n "
                                            "- *Example:* Chris Ray Gun: `https://www.twitch.tv/nemesiscrm` - use "
                                            "`nemesiscrm`\n "
                                            "For YouTube, use the username found in the url format "
                                            "`https://www.youtube.com/user/[username]`\n"
                                            "- *Example:* Phillip DeFranco: `https://www.youtube.com/user/sxephil` - "
                                            "use `sxephil`")
                return

            await self.bot.send_message(ctx.message.author,
                                        "**Rss usage**:\n"
                                        "`{0}rss <add/remove> <twitter/twitch/youtube> [username]`\n"
                                        "`{0}rss <list>`\n"
                                        "Example: `.feeds add twitter @pewdiepie` binds PieDiePie's twitter feed to the "
                                        "channel this is called from\n "
                                        "Call `.feeds help users` for user formatting info".format(
                                            self.bot.command_prefix))


async def send_update(bot: DiscordBot, server, new_feed: RssFeed):
    old_feed = server.get_feed(id=new_feed.id)  # type: RssFeed
    if old_feed:
        await bot.send_message('338508402689048587', 'updating feed for {}'.format(server.name))
        old_feed.update(new_feed)

        if isinstance(old_feed, TwitterFeed):
            await bot.send_message(discord.Object(id=old_feed.discord_channel_id),
                                   'https://twitter.com/{0}/status/{1}'.format(old_feed.handle, old_feed.last_tweet_id))

        elif isinstance(old_feed, TwitchFeed):
            await bot.send_message(discord.Object(id=old_feed.discord_channel_id),
                                   '{} is now streaming!\nhttps://www.twitch.tv/{}'
                                   ''.format(old_feed.title, old_feed.user_id))

        elif isinstance(old_feed, YouTubeFeed):
            await bot.send_message(discord.Object(id=old_feed.discord_channel_id),
                                   '@everyone\n{} has a new video!\n'
                                   'https://www.youtube.com/watch?v={}'
                                   ''.format(old_feed.title, old_feed.last_video_id))
        # write to storage after all of these
    else:
        server.feeds.append(new_feed)
        storage.write_feeds(server)


async def send_first_update(bot: DiscordBot, server, feed: RssFeed):
    feed.first_time = False
    if isinstance(feed, TwitterFeed):
        await bot.send_message(discord.Object(id=feed.discord_channel_id),
                               'Twitter feed for `@{0}` has now been enabled.\n'
                               'https://twitter.com/{0}/status/{1}'
                               ''.format(feed.handle, feed.last_tweet_id))

    elif isinstance(feed, TwitchFeed):
        await bot.send_message(discord.Object(id=feed.discord_channel_id),
                               'Twitch feed for {} has now been enabled. Here is the most '
                               'recent activity:\nhttps://www.twitch.tv/{}'
                               ''.format(feed.title, feed.user_id))

    elif isinstance(feed, YouTubeFeed):
        await bot.send_message(discord.Object(id=feed.discord_channel_id),
                               'Youtube feed for {} has now been enabled. All future '
                               'updates will now push `@everyone` mentions for '
                               'visibility. Here is the most recent video for this'
                               'channel:\n'
                               'https://www.youtube.com/watch?v={}'
                               ''.format(feed.title, feed.last_video_id))


def setup(bot):
    return Feeds(bot)
