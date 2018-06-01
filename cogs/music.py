import storage_manager as storage
from discordbot import DiscordBot
from music_queue import *
from util.global_util import *


class Music:
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.music_loading = False

        @self.bot.group(pass_context=True)
        async def music(ctx):
            pass

        @music.command(pass_context=True)
        async def play(ctx, *, arg: str = None):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if arg is None:
                if in_server.music.unpause():
                    await bot.send_message(ctx.message.channel, 'Music resumed :play_pause:')  # play after pause
                    return

                if in_server.music.is_playing():
                    await self.bot.say('Music is already playing')
                    return

                await in_server.music.play_next(ctx, in_server, self.bot)
                return

            await queue.callback(ctx, arg=arg)

            if in_server.music.is_playing():
                await self.bot.say('Music is already playing')
                return

            await in_server.music.play_next(ctx, in_server, self.bot)

        @music.command(pass_context=True)
        async def queue(ctx, *, arg: str = None):

            if not arg:
                arg = 'listall'

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if arg == 'clear':
                if not self.bot.has_high_permissions(ctx.message.author, in_server):
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
                        em.add_field(name='#{}: `{}`'.format(i + 1, track.title),
                                     value='Requested by {}'.format(track.requestee),
                                     inline=False)
                    await self.bot.say(embed=em)
                return

            if len(in_server.music) >= MUSIC_QUEUE_LIMIT:
                await self.bot.say('Queue is currently full.')
                return

            choice = self.is_num(arg)
            if choice:
                if not in_server.search_results:
                    await self.bot.say('No search in progress. Initiate a search with `{0}music search [query]`'.format(
                        self.bot.command_prefix))
                    return

                if choice < 1 or choice > len(in_server.search_results):
                    await self.bot.say('Please enter a number between 1 and {}'.format(len(in_server.search_results)))
                    return

                result = in_server.search_results[choice - 1]  # choice to index num

                url = 'https://www.youtube.com/watch?v={}'.format(result['id']['videoId'])
                track = in_server.music.add_track_raw(url, result['snippet']['title'], ctx.message.author.name)
                await self.bot.say('Track `{}` enqueued at spot #{} by `{}`'.format(track.title,
                                                                                  len(in_server.music),
                                                                                  track.requestee))
                in_server.search_results = None

            else:
                if arg[:4] == 'http':
                    track = await in_server.music.add_track(arg, ctx.message.author.name)  # type: Track
                    if track:
                        await self.bot.say('Track `{}` enqueued at spot #{} by `{}`'.format(track.title,
                                                                                          len(in_server.music),
                                                                                          track.requestee))
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
                        track = in_server.music.add_track_raw(url, result['snippet']['title'], ctx.message.author.name)
                        await self.bot.say('Track `{}` enqueued at spot #{} by `{}`'.format(track.title,
                                                                                          len(in_server.music),
                                                                                          track.requestee))
                    else:
                        global admins
                        await self.bot.say('Search failed. Please report to <@{}>'.format(admins[0]))  # admin, ie me

            storage.write_music(self.bot, in_server)

        @music.command(pass_context=True)
        async def pause(ctx):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if in_server.music.pause():
                await self.bot.say('Music paused :play_pause:')
            else:
                await self.bot.say('Music is already paused')

        @music.command(pass_context=True)
        async def resume(ctx):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if in_server.music.unpause():
                await self.bot.say('Music resumed :play_pause:')  # play after pause
            else:
                await self.bot.say('Music is already playing')

        @music.command(pass_context=True)
        async def skip(ctx):
            """if not self.self.bot.has_high_permissions(ctx.message.author):
                return"""

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            bot_vc = in_server.music.bot_voice_client  # type: discord.VoiceClient

            if not bot_vc:
                await self.bot.say('No music is playing.')
                return

            perm = self.bot.has_high_permissions(ctx.message.author, in_server)

            if not perm:
                if ctx.message.author.id in [x.id for x in bot_vc.channel.voice_members]:
                    needed = (len(bot_vc.channel.voice_members) - 1) * (2 / 3)  # subtract 1 to account for bot
                    if needed != int(needed):
                        needed = int(needed) + 1
                    if not in_server.music.vote_skip:
                        if in_server.music.vote_skip_register(ctx.message.author):
                            remaining = int(needed - 1)  # drop floating point
                            if remaining > 0:
                                await self.bot.say(
                                    '{} has started a vote skip. Type `{}music sk` to join the vote. A 2/3 majority '
                                    'passes ({} more vote{}).'.format(ctx.message.author.name,
                                                                      self.bot.command_prefix,
                                                                      remaining,
                                                                      '' if remaining == 1 else 's'))  # magical s
                    else:
                        if in_server.music.vote_skip_register(ctx.message.author):
                            remaining = int(needed - len(in_server.music.vote_skip))  # drop floating point
                            await self.bot.say('{} has joined the vote! {} more vote{} needed'
                                               ''.format(ctx.message.author.name,
                                                         remaining,
                                                         '' if remaining == 1 else 's'))  # more magic

            if perm or in_server.music.vote_skip_check(bot_vc.channel):
                await self.bot.say('Track skipped :fast_forward:')
                await in_server.music.skip()

        @music.command(pass_context=True)
        async def disconnect(ctx):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)
            on_vc = self.bot.voice_client_in(ctx.message.server)
            if on_vc:
                try:
                    in_server.music.player.stop()
                except AttributeError:
                    print('-No player to stop.')
                vc_name = on_vc.channel.name
                await on_vc.disconnect()
                in_server.music.player = None
                in_server.music.autoplay_channel = None
                in_server.music.bot_voice_client = None
                await self.bot.say('Disconnected from voice channel `{}`'.format(vc_name))
            else:
                await self.bot.say('Not connected to a voice channel')

        @music.command(pass_context=True)
        async def shuffle(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return
            in_server = self.bot.get_server(server=ctx.message.server)
            if len(in_server.music) > 0:
                random.shuffle(in_server.music.queue)
            await self.bot.say('Queue shuffled :twisted_rightwards_arrows:')

        @music.command(pass_context=True)
        async def search(ctx, *, arg):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

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
                out_str += '```\nPlease select an option by calling `{0}music queue #` or `{0}music play #`'.format(
                    self.bot.command_prefix)
                await self.bot.say(out_str)
            else:
                global admins
                await self.bot.say('Search failed. Please report to <@{0}>'.format(admins[0]))  # admin, ie me

        @music.command(pass_context=True)
        async def bind(ctx, channel: discord.Channel = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if not channel:
                channel = ctx.message.channel

            in_server.music.bind_chat = channel.id
            in_server.music_chat = channel.id
            storage.write_server_data(self.bot, in_server)

            await self.bot.say('Bound music commands to {0}'.format(channel.mention))

        @music.command(pass_context=True)
        async def unbind(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            in_server.music_chat = None
            in_server.music.bind_chat = None
            storage.write_server_data(self.bot, in_server)

            await self.bot.say('Unbound music commands.')

        @music.command(pass_context=True)
        async def current(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not in_server.music.player:
                await self.bot.say('There are no songs currently playing.')
                return

            em = discord.Embed(title='───────────────────────────', color=0xf44242)  # red
            em.set_author(name='Current Track',
                          icon_url='https://abs.twimg.com/emoji/v2/72x72/1f3b5.png',
                          url=in_server.music.player.url)
            em.add_field(name='Title', value=in_server.music.player.title)
            em.add_field(name='Requested By', value=in_server.music.current_track.requestee)
            em.add_field(name='Description', value=self.shorten_desc(in_server.music.player.description), inline=False)
            em.add_field(name='Uploader', value=in_server.music.player.uploader)
            em.add_field(name='Duration', value=self.time_from_sec(in_server.music.player.duration))
            em.add_field(name='View Count', value=in_server.music.player.views)

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
                      "Example: `{0}music p home resonance`\n"

            await self.bot.send_message(ctx.message.author, out_str.format(self.bot.command_prefix))

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


"""
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
                        await s.bot_voice_client.disconnect()
                        await bot.send_message(s.music_channel, 'Disconnecting due to inactivity. :sleeping:')
                        s.music_channel = None
                        s.bot_voice_client = None"""


def setup(bot):
    return Music(bot)
