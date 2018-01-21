import discord
from discord.ext import commands
from datetime import datetime
from global_util import *


class Feeds:
    def __init__(self, bot):
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

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            global rss_feeds  # *types of feeds
            global rss_timer
            if user[0] == '@':
                user = user[1:]  # takes @ off a username

            if platform.lower() not in rss_feeds:
                await self.bot.say('Sorry, ' + platform + ' is not a valid feed type.\n'
                                                          'Supported feeds include Twitch, Twitter and YouTube')
                return

            add_channel = ctx.message.channel

            if in_server:  # add rss
                if platform.lower() == 'twitter':
                    if get_rss(in_server, add_channel.id, user):  # if rss exists, cancel
                        await self.bot.say('User `@' + user + '` already has a Twitter feed on this channel')
                        return

                    in_server.rss.append({'uid': user,
                                          'channel': add_channel.id,
                                          'last_id': 'h',
                                          'type': 'twitter'})
                    writeRss(self.bot, in_server)
                    await self.bot.say('Added Twitter feed for `@' + user + '` to ' + add_channel.mention)
                    rss_timer = 70

                elif platform.lower() == 'twitch':
                    twitch_channel = twitch.get_channel_from_name(user)
                    if not twitch_channel:
                        await self.bot.say('Twitch user `' + user + '` does not exist')
                        return

                    if get_rss(in_server, add_channel.id, twitch_channel['_id']):
                        await self.bot.say('User `' + twitch_channel['display_name'] +
                                           '` already has a Twitch feed on this channel')
                        return

                    in_server.rss.append({'uid': twitch_channel['_id'],
                                          'channel': add_channel.id,
                                          'last_id': 'h',
                                          'type': 'twitch',
                                          'title': twitch_channel['display_name'],
                                          'user': user})
                    writeRss(self.bot, in_server)
                    await self.bot.say('Added Twitch feed for `' + twitch_channel['display_name'] +
                                       '` to ' + add_channel.mention)
                    rss_timer = 70

                elif platform.lower() == 'youtube':
                    if user[:4] == 'http':
                        token_start = user.find('user/')
                        if token_start == -1:
                            token_start = user.find('channel/')
                            if token_start == -1:
                                await self.bot.say('This link is invalid.')
                                return
                            token_start += len('channel/')
                            ytchannel = yt.get_channel_by_id(user[token_start:])
                            if not ytchannel:
                                await self.bot.say('This link is invalid.')
                                return

                        else:
                            token_start += len('user/')
                            ytchannel = yt.get_channel_by_name(user[token_start:])
                            if not ytchannel:
                                await self.bot.say('This link is invalid.')
                                return
                    else:
                        ytchannel = yt.get_channel_by_name(user)
                    if not ytchannel:
                        await self.bot.say('Youtube user `' + user + '` does not exist')
                        return

                    if get_rss(in_server, add_channel.id, ytchannel['id']):  # if rss exists, cancel
                        await self.bot.say('User `' + ytchannel['snippet'].title +
                                           '` already has a YouTube feed on this channel')
                        return

                    in_server.rss.append({'uid': ytchannel['id'],
                                          'channel': add_channel.id,
                                          'last_id': 'h',
                                          'last_time': 'h',
                                          'type': 'youtube',
                                          'title': ytchannel['snippet'].title})
                    writeRss(self.bot, in_server)
                    await self.bot.say('Added YouTube feed for `' + ytchannel['snippet'].title +
                                       '` to ' + add_channel.mention)
                    rss_timer = 70

        @rss.command(pass_context=True)
        async def remove(ctx, platform: str, user: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if user[0] == '@':
                user = user[1:]  # takes @ off a username

            if platform.lower() not in rss_feeds:
                await self.bot.say('Sorry, ' + platform + ' is not a valid feed type.\n'
                                                          'Supported feeds include Twitch, Twitter and YouTube')
                return

            add_channel = ctx.message.channel

            if platform.lower() == 'twitter':
                r_feed = get_rss(in_server, add_channel.id, user)
                if r_feed:
                    await self.bot.say('Removed Twitter feed for `@' + user + '` from ' + add_channel.mention)
                    in_server.rss.remove(r_feed)
                    writeRss(self.bot, in_server)
                else:
                    await self.bot.say('No Twitter feed for `@' + user + '` exists on this channel')

            elif platform.lower() == 'twitch':
                r_feed = None
                for r in in_server.rss:
                    if len(r) >= 5:
                        if r.title == user:
                            r_feed = r

                if r_feed:
                    await self.bot.say('Removed Twitch feed for `' + r_feed.title +
                                       '` from ' + add_channel.mention)
                    in_server.rss.remove(r_feed)
                    writeRss(self.bot, in_server)
                else:
                    await self.bot.say('No Twitch feed for `' + user +
                                       '` exists on this channel')

            elif platform.lower() == 'youtube':
                r_feed = None
                for r in in_server.rss:
                    if len(r) >= 5:
                        if r.title == user:
                            r_feed = r
                            break

                if r_feed:
                    await self.bot.say('Removed YouTube feed for `' + r_feed.title +
                                       '` from ' + add_channel.mention)
                    in_server.rss.remove(r_feed)
                    writeRss(self.bot, in_server)
                else:
                    await self.bot.say('No YouTube feed for `' + user +
                                       '` exists on this channel')

        @rss.command(pass_context=True)
        async def listall(ctx, arg: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if in_server.rss:
                out_str = ""
                for r in in_server.rss:
                    if r:
                        if arg == 'debug':
                            if r.type == 'twitter':
                                out_str += 'User `@{0}` has a Twitter feed on <#{1}>, LID: {2}\n'.format(r.uid,
                                                                                                         r.channel_id,
                                                                                                         r.last_id)
                            elif r.type == 'youtube':
                                out_str += 'User `{0}` has a YouTube feed on <#{1}>, LID: {2}, CHID: {3}\n'.format(
                                    r.title, r.channel_id, r.last_id, r.uid)
                            elif r.type == 'twitch':
                                out_str += 'User `{0}` has a Twitch feed on <#{1}>, LID: {2}, CHID: {3},\n'.format(
                                    r.title, r.channel_id, r.last_id, r.uid)
                        else:
                            if r.type == 'twitter':
                                out_str += 'User `@' + r.uid + '` has a Twitter feed on <#' + r.channel_id + '>\n'
                            elif r.type == 'youtube':
                                out_str += 'User `' + r.title + '` has a YouTube feed on <#' + r.channel_id + '>\n'
                            elif r.type == 'twitch':
                                out_str += 'User `' + r.title + '` has a Twitch feed on <#' + r.channel_id + '>\n'

                await self.bot.say(out_str)

        @rss.command(pass_context=True)
        async def force(ctx, feed_type: str, user: str):
            global rss_timer
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not checkAdmin(ctx.message.author.id):
                return

            for r in in_server.rss:
                if (feed_type.lower() == r.type) and (user == r.title):
                    r.last_id = 'none'
                    last_time = datetime.strptime(r.last_time[:r.last_time.find('.')], '%Y-%m-%dT%H:%M:%S')
                    last_time = last_time.replace(year=last_time.year - 1)
                    r.last_time = last_time.strftime('%Y-%m-%dT%H:%M:%S') + '.'
                    rss_timer = 70

        @rss.command(pass_context=True)
        async def help(ctx, arg: str = None):

            if not has_high_permissions(ctx.message.author, b=self.bot):
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
    t_feed = twitter_api.GetUserTimeline(screen_name=r.uid, count=1)
    if t_feed:
        last_tweet = t_feed[0]
        if last_tweet:
            if str(last_tweet.id) != str(r.last_id):
                if str(r.last_id) == 'h':
                    proxy_message(b.bot,
                                  r.channel_id,
                                  'Twitter feed for `@{0}` has now been enabled.\n'
                                  'https://twitter.com/{0}/status/{1}'.format(r.uid, str(last_tweet.id)))
                else:
                    if last_tweet.text:
                        if last_tweet.text[0] != '@':
                            proxy_message(b.bot,
                                          r.channel_id,
                                          'https://twitter.com/{0}/status/{1}'.format(r.uid, str(last_tweet.id)))
                    else:
                        proxy_message(b.bot,
                                      r.channel_id,
                                      'https://twitter.com/{0}/status/{1}'.format(r.uid, str(last_tweet.id)))

                r.last_id = str(last_tweet.id)
                writeRss(b.bot, s)  # bot, server


async def scrape_youtube(b, s, r):
    search = None
    try:
        search = await yt.get_channel_videos(r.uid, 1)
    except Exception as e:
        print(e)
    if search:
        last_vid = search[0]
        if last_vid['id']['videoId'] != str(r.last_id):
            if str(r.last_id) == 'h':
                proxy_message(b.bot, r.channel_id,
                              'Youtube feed for {} has now been enabled. All future '
                              'updates will now push `@everyone` mentions for '
                              'visibility. Here is the most recent video for this'
                              'channel:\n'
                              'https://www.youtube.com/watch?v={}'
                              ''.format(str(r.title), last_vid['id']['videoId']))
                r.last_time = last_vid['snippet']['publishedAt']
                r.last_id = last_vid['id']['videoId']
                writeRss(b.bot, s)  # bot, server
            else:
                dtime_seq = last_vid['snippet']['publishedAt']
                this_time = datetime.strptime(dtime_seq[:dtime_seq.find('.')],
                                              '%Y-%m-%dT%H:%M:%S')
                last_time = datetime.strptime(r.last_time[:r.last_time.find('.')],
                                              '%Y-%m-%dT%H:%M:%S')
                if this_time > last_time:
                    proxy_message(b.bot, r.channel_id,
                                  '@everyone\n{} has a new video!\n'
                                  'https://www.youtube.com/watch?v={}'
                                  ''.format(str(r.title), last_vid['id']['videoId']))
                    r.last_time = last_vid['snippet']['publishedAt']
                    r.last_id = last_vid['id']['videoId']
                    writeRss(b.bot, s)  # bot, server


async def scrape_twitch(b, s, r):
    stream = None
    try:
        stream = await twitch.get_stream(r.uid)
    except ValueError as e:
        print(e)
    if stream:
        if (str(stream['stream']['_id']) != str(r.last_id)) and (str(r.last_id) != 'h') and (
                    str(r.last_id) != 'd'):
            proxy_message(b.bot, r.channel_id,
                          '{} is now streaming!\nhttps://www.twitch.tv/{}'
                          ''.format(str(r.title), r.user))
            r.last_id = str(stream['stream']['_id'])
            writeRss(b.bot, s)  # bot, server
    else:
        if str(r.last_id) == 'h':
            proxy_message(b.bot, r.channel_id,
                          'Twitch feed for {} has now been enabled. Here is the most '
                          'recent activity:\nhttps://www.twitch.tv/{}'
                          ''.format(str(r.title), r.user))
            r.last_id = '111000'  # doesn't matter what this is
            writeRss(b.bot, s)


def setup(bot):
    return Feeds(bot)
