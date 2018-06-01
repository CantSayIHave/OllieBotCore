from datetime import datetime

import storage_manager as storage
from discordbot import DiscordBot
from util import global_util
from util.containers import *


class Feeds:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        @self.bot.group(pass_context=True)
        async def rss(ctx):
            pass

        # Creates an rss feed in [User | Channel ID | Last Tweet ID] format
        @rss.command(pass_context=True)
        async def add(ctx, platform: str, user: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if user[0] == '@':
                user = user[1:]  # takes @ off a username

            if platform.lower() not in global_util.rss_feeds:
                await self.bot.say('Sorry, ' + platform + ' is not a valid feed type.\n'
                                                          'Supported feeds include Twitch, Twitter and YouTube')
                return

            add_channel = ctx.message.channel

            if in_server:  # add rss
                if platform.lower() == 'twitter':
                    if in_server.get_rss(add_channel, uid=user):  # if rss exists, cancel
                        await self.bot.say('User `@{}` already has a Twitter feed on this channel'.format(user))
                        return

                    in_server.rss.append(Feed(uid=user,
                                              channel_id=add_channel.id,
                                              last_id='h',
                                              type='twitter'))
                    storage.write_rss(self.bot, in_server)
                    await self.bot.say('Added Twitter feed for `@{}` to {}'.format(user, add_channel.mention))
                    global_util.rss_timer = 70

                elif platform.lower() == 'twitch':
                    twitch_channel = await global_util.twitch.get_channel_from_name(user)
                    if not twitch_channel:
                        await self.bot.say('Twitch user `{}` does not exist'.format(user))
                        return

                    if in_server.get_rss(add_channel, uid=twitch_channel['_id']):
                        await self.bot.say('User `{}` already has a Twitch feed on this channel'
                                           ''.format(twitch_channel['display_name']))
                        return

                    in_server.rss.append(Feed(uid=twitch_channel['_id'],
                                              channel_id=add_channel.id,
                                              last_id='h',
                                              type='twitch',
                                              title=twitch_channel['display_name'],
                                              user=user))
                    storage.write_rss(self.bot, in_server)
                    await self.bot.say('Added Twitch feed for `' + twitch_channel['display_name'] +
                                       '` to ' + add_channel.mention)
                    global_util.rss_timer = 70

                elif platform.lower() == 'youtube':
                    if user[:4] == 'http':
                        token_start = user.find('user/')  # what is this absolute nonsense
                        if token_start == -1:
                            token_start = user.find('channel/')
                            if token_start == -1:
                                await self.bot.say('This link is invalid.')  # please don't judge me.
                                return
                            token_start += len('channel/')
                            ytchannel = await global_util.yt.get_channel_by_id(user[token_start:])
                            if not ytchannel:
                                await self.bot.say('This link is invalid.')
                                return

                        else:
                            token_start += len('user/')
                            ytchannel = await global_util.yt.get_channel_by_name(user[token_start:])
                            if not ytchannel:
                                await self.bot.say('This link is invalid.')
                                return
                    else:
                        ytchannel = await global_util.yt.get_channel_by_name(user)
                    if not ytchannel:
                        await self.bot.say('Youtube user `{}` does not exist'.format(user))
                        return

                    if in_server.get_rss(add_channel, uid=ytchannel['id']):  # if rss exists, cancel
                        await self.bot.say('User `{}` already has a YouTube feed on this channel'
                                           ''.format(ytchannel['snippet']['title']))
                        return

                    in_server.rss.append(Feed(uid=ytchannel['id'],
                                              channel_id=add_channel.id,
                                              last_id='h',
                                              last_time='h',
                                              type='youtube',
                                              title=ytchannel['snippet']['title']))

                    storage.write_rss(self.bot, in_server)
                    await self.bot.say('Added YouTube feed for `' + ytchannel['snippet']['title'] +
                                       '` to ' + add_channel.mention)
                    global_util.rss_timer = 70

        @rss.command(pass_context=True)
        async def remove(ctx, platform: str, user: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if user[0] == '@':
                user = user[1:]  # takes @ off a username

            if platform.lower() not in global_util.rss_feeds:
                await self.bot.say('Sorry, {} is not a valid feed type.\n'
                                   'Supported feeds include Twitch, Twitter and YouTube'.format(platform))
                return

            feed_channel = ctx.message.channel

            if platform.lower() == 'twitter':
                r_feed = in_server.get_rss(feed_channel, uid=user)

                if r_feed:
                    await self.bot.say('Removed Twitter feed for `@{}` from {}'.format(user, feed_channel.mention))
                    in_server.rss.remove(r_feed)
                    storage.write_rss(self.bot, in_server)
                else:
                    await self.bot.say('No Twitter feed for `@{}` exists on this channel'.format(user))

            elif platform.lower() == 'twitch':
                r_feed = in_server.get_rss(feed_channel, title=user, wide_search=True)

                if r_feed:
                    await self.bot.say(
                        'Removed Twitch feed for `{}` from {}'.format(r_feed.title, feed_channel.mention))
                    in_server.rss.remove(r_feed)
                    storage.write_rss(self.bot, in_server)
                else:
                    await self.bot.say('No Twitch feed for `{}` exists on this channel'.format(user))

            elif platform.lower() == 'youtube':
                r_feed = in_server.get_rss(feed_channel, title=user, wide_search=True)

                if r_feed:
                    await self.bot.say('Removed YouTube feed for '
                                       '`{}` from {}'.format(r_feed.title, feed_channel.mention))
                    in_server.rss.remove(r_feed)
                    storage.write_rss(self.bot, in_server)
                else:
                    await self.bot.say('No YouTube feed for `{}` exists on this channel'.format(user))

        @rss.command(pass_context=True)
        async def listall(ctx, arg: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if in_server.rss:
                out_str = ""
                for r in in_server.rss:  # type: Feed
                    if r:
                        if arg == 'debug':
                            if r.type == 'twitter':
                                out_str += 'User `@{}` has a Twitter feed on <#{}>, LID: {}\n'.format(r.uid,
                                                                                                      r.channel_id,
                                                                                                      r.last_id)
                            elif r.type == 'youtube':
                                out_str += 'User `{}` has a YouTube feed on <#{}>, LID: {}, CHID: {}\n'.format(
                                    r.title, r.channel_id, r.last_id, r.uid)
                            elif r.type == 'twitch':
                                out_str += 'User `{}` has a Twitch feed on <#{}>, LID: {}, CHID: {},\n'.format(
                                    r.title, r.channel_id, r.last_id, r.uid)
                        else:
                            if r.type == 'twitter':
                                out_str += 'User `@{}` has a Twitter feed on <#{}>\n'.format(r.uid, r.channel_id)
                            elif r.type == 'youtube':
                                out_str += 'User `{}` has a YouTube feed on <#{}>\n'.format(r.title, r.channel_id)
                            elif r.type == 'twitch':
                                out_str += 'User `{}` has a Twitch feed on <#{}>\n'.format(r.title, r.channel_id)

                await self.bot.say(out_str)

        @rss.command(pass_context=True)
        async def force(ctx, feed_type: str, user: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.check_admin(ctx.message.author):
                return

            for r in in_server.rss:
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
            in_server.rss = []
            storage.write_rss(self.bot, in_server)

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
                                        "Example: `.rss add twitter @pewdiepie` binds PieDiePie's twitter feed to the "
                                        "channel this is called from\n "
                                        "Call `.rss help users` for user formatting info".format(
                                            self.bot.command_prefix))


def scrape_twitter(b, s, r):
    t_feed = global_util.twitter_api.GetUserTimeline(screen_name=r.uid, count=1)
    if t_feed:
        last_tweet = t_feed[0]
        if last_tweet:
            if str(last_tweet.id) != str(r.last_id):
                if str(r.last_id) == 'h':
                    global_util.proxy_message(b,
                                              r.channel_id,
                                              'Twitter feed for `@{0}` has now been enabled.\n'
                                              'https://twitter.com/{0}/status/{1}'.format(r.uid, str(last_tweet.id)))
                else:
                    if last_tweet.text:
                        if last_tweet.text[0] != '@':
                            global_util.proxy_message(b,
                                                      r.channel_id,
                                                      'https://twitter.com/{0}/status/{1}'.format(r.uid,
                                                                                                  str(last_tweet.id)))
                    else:
                        global_util.proxy_message(b,
                                                  r.channel_id,
                                                  'https://twitter.com/{0}/status/{1}'.format(r.uid,
                                                                                              str(last_tweet.id)))

                r.last_id = str(last_tweet.id)
                storage.write_rss(b, s)  # bot, server


async def scrape_youtube(b, s, r):
    search = None
    try:
        search = await global_util.yt.get_channel_videos(r.uid, 1)
    except Exception as e:
        print(e)
    if search:
        last_vid = search[0]
        if last_vid['id']['videoId'] != str(r.last_id):
            if str(r.last_id) == 'h':
                global_util.proxy_message(b, r.channel_id,
                                          'Youtube feed for {} has now been enabled. All future '
                                          'updates will now push `@everyone` mentions for '
                                          'visibility. Here is the most recent video for this'
                                          'channel:\n'
                                          'https://www.youtube.com/watch?v={}'
                                          ''.format(str(r.title), last_vid['id']['videoId']))
                r.last_time = last_vid['snippet']['publishedAt']
                r.last_id = last_vid['id']['videoId']
                storage.write_rss(b, s)  # bot, server
            else:
                dtime_seq = last_vid['snippet']['publishedAt']
                this_time = datetime.strptime(dtime_seq[:dtime_seq.find('.')],
                                              '%Y-%m-%dT%H:%M:%S')
                last_time = datetime.strptime(r.last_time[:r.last_time.find('.')],
                                              '%Y-%m-%dT%H:%M:%S')
                if this_time > last_time:
                    global_util.proxy_message(b, r.channel_id,
                                              '@everyone\n{} has a new video!\n'
                                              'https://www.youtube.com/watch?v={}'
                                              ''.format(str(r.title), last_vid['id']['videoId']))
                    r.last_time = last_vid['snippet']['publishedAt']
                    r.last_id = last_vid['id']['videoId']
                    storage.write_rss(b, s)  # bot, server


async def scrape_twitch(b, s, r):
    stream = None
    try:
        stream = await global_util.twitch.get_stream(r.uid)
    except ValueError as e:
        print(e)
    if stream:
        if (str(stream['stream']['_id']) != str(r.last_id)) and (str(r.last_id) != 'h') and (
                    str(r.last_id) != 'd'):
            global_util.proxy_message(b, r.channel_id,
                                      '{} is now streaming!\nhttps://www.twitch.tv/{}'
                                      ''.format(str(r.title), r.user))
            r.last_id = str(stream['stream']['_id'])
            storage.write_rss(b, s)  # bot, server
    else:
        if str(r.last_id) == 'h':
            global_util.proxy_message(b.bot, r.channel_id,
                                      'Twitch feed for {} has now been enabled. Here is the most '
                                      'recent activity:\nhttps://www.twitch.tv/{}'
                                      ''.format(str(r.title), r.user))
            r.last_id = '111000'  # doesn't matter what this is
            storage.write_rss(b, s)


def setup(bot):
    return Feeds(bot)
