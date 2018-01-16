import discord
from discord.ext import commands
import random
from global_util import *


class Music:
    def __init__(self, bot):
        self.bot = bot
        self.music_loading = False

        @self.bot.group(pass_context=True)
        async def music(ctx):
            """music is a group"""

        @music.command(pass_context=True)
        async def play(ctx, *, arg: str = None):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if arg is None:
                await self.play_next(in_server, ctx)
                return

            choice = self.is_num(arg)
            if choice:
                if not in_server.search_results:
                    await self.bot.say('No search in progress. Initiate a search with `{0}music search [query]`'.format(
                        self.bot.command_prefix))
                    return

                if choice < 1 or choice > len(in_server.search_results):
                    await self.bot.say('Please enter a number between 1 and {0}'.format(len(in_server.search_results)))
                    return

                result = in_server.search_results[choice - 1]  # choice to index num

                url = 'https://www.youtube.com/watch?v={0}'.format(result['id']['videoId'])
                in_server.add_music_raw(url, result['snippet']['title'], ctx.message.author.name)
                place = in_server.get_track_pos(url)
                await self.bot.say(
                    'Track `' + result['snippet']['title'] + '` enqueued at spot #' + str(place) +
                    ' by `' + ctx.message.author.name + '`')
                await self.play_next(in_server, ctx)
                in_server.search_results = None

            else:
                if arg[:4] == 'http':
                    vid_info = await in_server.add_music_url(arg, ctx.message.author.name)
                    if vid_info:
                        place = in_server.get_track_pos(arg)
                        await self.bot.say(
                            'Track `' + vid_info['snippet']['title'] + '` enqueued at spot #' + str(place) +
                            ' by `' + ctx.message.author.name + '`')
                        await self.play_next(in_server, ctx)
                    else:
                        await self.bot.say('Video url is invalid :no_entry_sign:')
                        return
                else:
                    result = None
                    try:
                        result = await yt.search_videos(arg, 1)
                        result = result[0]
                    except Exception as e:
                        print('Bot play search failed: ' + str(e))
                    if result:
                        url = 'https://www.youtube.com/watch?v={}'.format(result['id']['videoId'])
                        in_server.add_music_raw(url, result['snippet']['title'], ctx.message.author.name)
                        place = in_server.get_track_pos(url)
                        await self.bot.say(
                            'Track `' + result['snippet']['title'] + '` enqueued at spot #' + str(place) +
                            ' by `' + ctx.message.author.name + '`')
                        if in_server.music_player:
                            if in_server.music_player.is_done() and not in_server.music_player.is_playing():
                                await self.play_next(in_server, ctx)  # hopefully keep multiple instances from forming
                        else:
                            await self.play_next(in_server, ctx)
                    else:
                        global admins
                        await self.bot.say('Search failed. Please report to <@{0}>'.format(admins[0]))  # admin, ie me

            writeMusic(self.bot, in_server)

        @music.command(pass_context=True)
        async def queue(ctx, *, arg: str):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if arg == 'clear':
                if not has_high_permissions(ctx.message.author, in_server):
                    return
                in_server.music.clear()
                await self.bot.say('Cleared queue')
                return

            if arg == 'listall':
                if len(in_server.music) < 1:
                    await self.bot.say(
                        'No tracks in queue. Call `{0}music queue` or `{0}music play` to add some'.format(
                            self.bot.command_prefix))
                else:
                    em = discord.Embed(title='───────────────────────────', color=0xf4df41)  # gold
                    em.set_author(name='Tracks in Queue', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f3b6.png')
                    for i, track in enumerate(in_server.music):
                        em.add_field(name='#{0}: `{1}`'.format(i + 1, track['title']),
                                     value='Requested by {}'.format(track['user']),
                                     inline=False)
                    await self.bot.say(embed=em)
                return

            choice = self.is_num(arg)
            if choice:
                if not in_server.search_results:
                    await self.bot.say('No search in progress. Initiate a search with `{0}music search [query]`'.format(
                        self.bot.command_prefix))
                    return

                if choice < 1 or choice > len(in_server.search_results):
                    await self.bot.say('Please enter a number between 1 and {0}'.format(len(in_server.search_results)))
                    return

                result = in_server.search_results[choice - 1]  # choice to index num

                url = 'https://www.youtube.com/watch?v={0}'.format(result['id']['videoId'])
                in_server.add_music_raw(url, result['snippet']['title'], ctx.message.author.name)
                place = in_server.get_track_pos(url)
                await self.bot.say(
                    'Track `' + result['snippet']['title'] + '` enqueued at spot #' + str(place) +
                    ' by `' + ctx.message.author.name + '`')
                in_server.search_results = None

            else:
                if arg[:4] == 'http':
                    vid_info = await in_server.add_music_url(arg, ctx.message.author.name)
                    if vid_info:
                        place = in_server.get_track_pos(arg)
                        await self.bot.say(
                            'Track `' + vid_info['snippet']['title'] + '` enqueued at spot #' + str(place) +
                            ' by `' + ctx.message.author.name + '`')
                    else:
                        await self.bot.say('Video url is invalid :no_entry_sign:')
                        return
                else:
                    result = None
                    try:
                        result = await yt.search_videos(arg, 1)
                        result = result[0]
                    except Exception as e:
                        print('Bot play search failed: ' + str(e))
                    if result:
                        url = 'https://www.youtube.com/watch?v={0}'.format(result['id']['videoId'])
                        in_server.add_music_raw(url, result['snippet']['title'], ctx.message.author.name)
                        place = in_server.get_track_pos(url)
                        await self.bot.say(
                            'Track `' + result['snippet']['title'] + '` enqueued at spot #' + str(place) +
                            ' by `' + ctx.message.author.name + '`')
                    else:
                        global admins
                        await self.bot.say('Search failed. Please report to <@{0}>'.format(admins[0]))  # admin, ie me

            writeMusic(self.bot, in_server)

        @music.command(pass_context=True)
        async def pause(ctx):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)
            if in_server.music_player:
                in_server.music_player.pause()
                await self.bot.say('Music paused :play_pause:')

        @music.command(pass_context=True)
        async def skip(ctx):
            """if not self.has_high_permissions(ctx.message.author):
                return"""

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            bot_vc = self.bot.voice_client_in(ctx.message.server)  # type: discord.VoiceClient

            if not bot_vc:
                await self.bot.say('No music is playing.')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            perm = has_high_permissions(ctx.message.author, in_server)

            if not perm:
                if ctx.message.author.id in [x.id for x in bot_vc.channel.voice_members]:
                    needed = len(bot_vc.channel.voice_members) * (2 / 3)
                    if needed != int(needed):
                        needed = int(needed)
                    else:
                        needed -= 1
                    if not in_server.vote_skip:
                        in_server.vote_skip_register(ctx.message.author)
                        remaining = needed - 1
                        await self.bot.say(
                            '{} has started a vote skip. Type `{}music sk` to join the vote. A 2/3 majority '
                            'passes ({} more vote{}).'.format(ctx.message.author.name,
                                                              self.bot.command_prefix,
                                                              remaining,
                                                              '' if remaining == 1 else 's'))  # magical s
                        in_server.vote_skip_register(ctx.message.author)
                    else:
                        if in_server.vote_skip_register(ctx.message.author):
                            remaining = needed - len(in_server.vote_skip)
                            await self.bot.say('{} has joined the vote! {} more vote{} needed'
                                               ''.format(ctx.message.author.name,
                                                         remaining,
                                                         '' if remaining == 1 else 's'))  # more magic

            if perm or in_server.vote_skip_check(bot_vc.channel):
                in_server.vote_skip_clear()
                if in_server.music_player:
                    in_server.music_player.stop()
                    in_server.music_player = None  # important - prevents autoplay loop from interfering
                await self.bot.say('Track skipped :fast_forward:')
                await self.play_next(in_server, ctx)
                writeMusic(self.bot, in_server)

        @music.command(pass_context=True)
        async def disconnect(ctx):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)
            on_vc = self.bot.voice_client_in(ctx.message.server)
            if on_vc:
                vc_name = on_vc.channel.name
                await on_vc.disconnect()
                try:
                    in_server.music_player.stop()
                except AttributeError:
                    print('-No player to stop.')
                in_server.music_player = None
                in_server.music_channel = None
                in_server.bot_voice_client = None
                await self.bot.say('Disconnected from voice channel `{}`'.format(vc_name))
            else:
                await self.bot.say('Not connected to a voice channel')

        @music.command(pass_context=True)
        async def shuffle(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return
            in_server = get_server(ctx.message.server.id, self.bot)
            if len(in_server.music) > 0:
                random.shuffle(in_server.music)
            await self.bot.say('Queue shuffled :twisted_rightwards_arrows:')

        @music.command(pass_context=True)
        async def search(ctx, *, arg):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            results = None
            try:
                results = await yt.search_videos(arg, 10)
            except Exception as e:
                print('Bot play search failed: ' + str(e))
            if results:
                in_server.search_results = results
                out_str = "**Youtube Search**\n" \
                          "Query: `{0}`\n```Results:\n\n".format(arg)
                for i, r in enumerate(results):
                    title = self.shorten_str(r['snippet']['title'], 30)
                    ch_title = self.shorten_str(r['snippet']['channelTitle'], 20)
                    out_str += ' {0}. {1} by {2}\n\n'.format(i + 1,
                                                             title,
                                                             ch_title)
                    # out_str += out_line + self.dynamic_tab(out_line, 68) + "\n" + self.dynamic_tab("", 60) + "`\n"
                out_str += '```\nPlease select an option by calling `{0}music queue #` or `{0}music play #`'.format(
                    self.bot.command_prefix)
                await self.bot.say(out_str)
            else:
                global admins
                await self.bot.say('Search failed. Please report to <@{0}>'.format(admins[0]))  # admin, ie me

        @music.command(pass_context=True)
        async def bind(ctx, channel: discord.Channel):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            in_server.music_chat = channel

            await self.bot.say('Bound music commands to {0}'.format(channel.mention))

        @music.command(pass_context=True)
        async def unbind(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            in_server.music_chat = None

            await self.bot.say('Unbound music commands.')

        @music.command(pass_context=True)
        async def current(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not in_server.music_player:
                await self.bot.say('There are no songs currently playing.')
                return

            em = discord.Embed(title='───────────────────────────', color=0xf44242)  # red
            em.set_author(name='Current Track',
                          icon_url='https://abs.twimg.com/emoji/v2/72x72/1f3b5.png',
                          url=in_server.music_player.url)
            em.add_field(name='Title', value=in_server.music_player.title)
            em.add_field(name='Requested By', value=in_server.current_track['user'])
            em.add_field(name='Description', value=self.shorten_desc(in_server.music_player.description), inline=False)
            em.add_field(name='Uploader', value=in_server.music_player.uploader)
            em.add_field(name='Duration', value=self.time_from_sec(in_server.music_player.duration))
            em.add_field(name='View Count', value=in_server.music_player.views)

            await self.bot.say(embed=em)

        @music.command(pass_context=True)
        async def help(ctx):
            out_str = '**Music usage**:\n' \
                      '`{0}music <play/queue> [youtube link/search query/search result #]`\n' \
                      '`{0}music <queue> <clear/list>`\n' \
                      '`{0}music <search> [search query]`\n' \
                      '`{0}music <play/pause/skip/shuffle/current/disconnect>`\n\n' \
                      'Full youtube-to-voice music interface. To use `{0}music play`, you must be in a voice ' \
                      'channel.\n' \
                      '*Note:* The only difference between `{0}music queue` and `{0}music play` is that the latter ' \
                      'starts playing the queue. Both will add music to the queue.\n' \
                      '*Note:* `queue clear` is moderator-only.\n\n' \
                      'The command `{0}music <play/queue>` takes either a youtube link, a query to search youtube ' \
                      'with, or a search result number (1-10). If provided a query, the first result will be added ' \
                      'to the queue.\n' \
                      'Examples:\n' \
                      '`{0}music play https://www.youtube.com/watch?v=dQw4w9WgXcQ`\n' \
                      '`{0}music queue flume you and me`\n' \
                      '`{0}music play 2`\n' \
                      '*Note:* If a search has not been initiated, passing a number will not add anything.\n\n' \
                      'To initiate a search, call `{0}music <search> [search query]`, and the first 10 results ' \
                      'will be displayed. You may then select a choice with `play` or `queue`.\n\n' \
                      'Use `current` to get the current track info.\n\n' \
                      'Lastly, each command has shortened call methods for ease-of-use if desired:\n' \
                      '`play:          p`\n' \
                      '`queue:         q`\n' \
                      '`queue clear:   qc or cq`\n' \
                      '`queue list:    ql or lq`\n' \
                      '`search:        se`\n' \
                      '`pause:         ps`\n' \
                      '`skip:          sk`\n' \
                      '`shuffle:       sh`\n' \
                      '`disconnect:    d`\n' \
                      '`current:       c`\n\n' \
                      "Example: `{0}music p ain't no rest for the triggered`\n"

            await self.bot.send_message(ctx.message.author, out_str.format(self.bot.command_prefix))

    async def play_next(self, in_server, ctx):

        if not isinstance(ctx.message.author, discord.Member):
            await self.bot.send_message(ctx.message.channel, 'Music does not work in private messaging. Please join a '
                                                             'voice channel on a server to proceed')
            return False

        vc = ctx.message.author.voice_channel
        if not vc and not has_high_permissions(ctx.message.author, in_server):
            await self.bot.send_message(ctx.message.channel, 'You are not in a voice channel. Please join one to call '
                                                             '`{0}music play`'.format(self.bot.command_prefix))
            return False

        if in_server.music_player:
            if not in_server.music_player.is_done():
                if not in_server.music_player.is_playing():
                    in_server.music_player.resume()
                    await self.bot.send_message(ctx.message.channel, 'Music resumed :play_pause:')  # play after pause
                    return
                await self.bot.send_message(ctx.message.channel, 'Music is already playing.')
                return False

        if not vc:
            await self.bot.send_message(ctx.message.channel, 'Please join a voice channel to call this.')
            return

        bot_vc = self.bot.voice_client_in(ctx.message.server)
        if not bot_vc:
            bot_vc = await self.bot.join_voice_channel(vc)
            await self.bot.send_message(ctx.message.channel, 'Joined and bound to `{0}`'.format(bot_vc.channel.name))
        next_up = in_server.get_music_url()
        if next_up:  # Create streamer for next song and play
            if self.music_loading:
                return True
            self.music_loading = True
            in_server.music_player = await bot_vc.create_ytdl_player(next_up['url'], before_options="-reconnect 1")
            self.music_loading = False

            in_server.music_player.start()
            in_server.music_player.volume = 1.0

            in_server.music_channel = ctx.message.channel
            in_server.bot_voice_client = bot_vc
            await self.bot.send_message(ctx.message.channel,
                                        'Track `{0}` enqueued by `{1}` is now playing.'.format(next_up['title'],
                                                                                               next_up['user']))
        else:
            await self.bot.send_message(ctx.message.channel,
                                        'There are no songs in the queue. Add with '
                                        '`{0}music queue` or `{0}music play`'.format(self.bot.command_prefix))

    @staticmethod
    def shorten_str(word: str, new_length: int):
        if len(word) <= new_length:
            return word
        short = word[:new_length]
        return short[:len(short) - 3] + '...'

    @staticmethod
    def is_num(text: str):
        try:
            num = int(text)
            return num
        except ValueError:
            return None

    def shorten_desc(self, text: str):
        if len(text) >= 400:
            text = text[:400] + '...'
        if text.count('\n') > 8:
            end = self.get_index_at(text, '\n', 8)
            text = text[:end] + '...'
        return text

    # Returns index of nth occurrence
    @staticmethod
    def get_index_at(text: str, key: str, at_index: int):
        occurrence = 0
        on_index = 0
        for c in text:
            on_index += 1
            if c == key:
                occurrence += 1
            if occurrence == at_index:
                return on_index

    @staticmethod
    def time_from_sec(t_seconds: int):
        minutes = int(t_seconds / 60)
        seconds = t_seconds - (minutes * 60)
        hours = int(minutes / 60)

        out_seconds = str(seconds)

        if seconds < 10:
            out_seconds = '0' + out_seconds

        out_minutes = str(minutes)

        if hours > 0:
            minutes = minutes - (hours * 60)

            if minutes < 10:
                out_minutes = '0' + out_minutes

        if hours > 0:
            return '{}:{}:{}'.format(str(hours), out_minutes, out_seconds)
        else:
            return '{}:{}'.format(out_minutes, out_seconds)


async def autoplay_next(bot, in_server: Server):
    in_server.vote_skip_clear()
    next_up = in_server.get_music_url()
    if next_up:
        bot_vc = in_server.bot_voice_client
        if in_server.music_loading:
            return True
        in_server.music_loading = True
        in_server.music_player = await bot_vc.create_ytdl_player(next_up['url'],
                                                                 before_options="-reconnect 1")
        in_server.music_loading = False
        in_server.music_player.start()
        in_server.music_player.volume = 1.0
        await bot.send_message(in_server.music_channel,
                               'Track `{0}` enqueued by `{1}` is now playing.'.format(next_up['title'],
                                                                                      next_up['user']))
        return True
    else:
        return False


async def music_autoplay(s: Server, bot):  # bot is discord bot
    if s.music_player:
        if s.music_player.is_done() and not s.music_player.is_playing():
            if s.music_channel and s.bot_voice_client:
                if not (await autoplay_next(bot, s)):
                    if s.music_timeout():
                        s.bot_voice_client.disconnect()
                        await bot.send_message(s.music_channel, 'Disconnecting due to inactivity. :sleeping:')
                        s.music_channel = None
                        s.bot_voice_client = None


def setup(bot):
    return Music(bot)
