import asyncio

import storage_manager as storage
from cogs import feeds
from discordbot import DiscordBot
from server import Server
from util import global_util
from util.global_util import *

random.seed()

"""
DONE:
add server to bot - add 1st mod
add quotes
add server AUTOMAGICALLY
replaced mention w/ id
remove server from bot
rename server
remove quotes
quote timer
reeeeeeee
rss
quote author
custom help
add autoplay
add search
implement help -> inbox
add PM blocks
add shortened commands
add shuffle
add help
wiki
reee response
emote suggest
music bind
repl
block commands
timeout commands
restructure build from file
proxy message sending
restructure
roll
bun
musac
 add timeout
paginator class
music redo
sound converters
add bot shutdown and restart (eh)
cdn
fix strawpoll
virtalenv
cat
boop

TODO:
cuddle

rss server
message freq stats
RemindMe (maybe)
command control (maybe) (kinda did)

"""

async_exit_timer = 0

sync_exit_timer = 0

sync_shutdown = False

startup_extensions = ["server_utils", "feeds", "fun", "responses", "music", "think", "sense", "help", "photoshop", "admin"]

startup_extensions = ['cogs.{}'.format(x) for x in startup_extensions]

replace_chars = [('“', '"'), ('”', '"'), ('‘', "'"), ('’', "'")]

command_mappings = {'b-ify': 'b_ify',
                    'nick-all': 'nick_all',
                    '8ball': 'eight_ball',
                    'eightball': 'eight_ball'}


class BotManager:
    def __init__(self):
        self.bots = []

    def add(self, bot: DiscordBot):
        bot.bot_list = self  # every bot can access the bot list
        self.bots.append(bot)

    def remove(self, bot: DiscordBot):
        self.bots.remove(bot)

    def run_all(self, loop):
        for b in self.bots:  # type:DiscordBot
            loop.create_task(b.start(b.token))

    def __len__(self):
        return len(self.bots)

    def __iter__(self):
        return self.bots.__iter__()

    def __getitem__(self, item):
        if type(item) is str:
            for b in self.bots:
                if b.name == item:
                    return b
        else:
            return self.bots[item]
        raise KeyError('Bot with name `{}` not found.'.format(item))

    def __str__(self):
        return 'BotManager:{}'.format(self.bots)

    def __repr__(self):
        return str(self)


async def delete_messages():
    while True:
        await asyncio.sleep(1)
        for d in global_util.delete_queue:  # type: DeleteMessage
            d.timer -= 1
            if d.timer <= 0:
                try:
                    await d.bot.delete_message(d.message)
                except Exception:
                    print('Failed to delete a message.')
                global_util.delete_queue.remove(d)

        for c in global_util.coro_queue:  # type: TimedFuture
            c.timer -= 1
            if c.timer <= 0:
                try:
                    await c.coro
                except Exception as e:
                    print('Coro out failed at: {}'.format(e))
                global_util.coro_queue.remove(c)


async def background_async():
    global bots, loop
    while True:
        await asyncio.sleep(10)
        try:
            while len(global_util.out_messages) > 0:
                try:
                    msg_out = global_util.out_messages.popleft()  # type: ProxyMessage
                    if msg_out.embed is None:
                        await msg_out.bot.send_message(msg_out.channel, msg_out.content)
                    else:
                        await msg_out.bot.send_message(msg_out.channel, em=msg_out.embed)
                except Exception as e:
                    print('Proxy sender failed at {}'.format(e))

            for b in bots:
                for s in b.local_servers:  # type: Server
                    for c in s.spam_timers:
                        if s.spam_timers[c] > 0:
                            s.spam_timers[c] -= 10

                    s.response_lib.dec_spam_timers(10)

                    """
                    try:
                        await music.music_autoplay(s, b.bot)
                    except Exception as e:
                        print('Music autoplay failed at: ' + str(e))"""

            print('Alive ' + str(global_util.alive_timer))

            global_util.alive_timer += 1
            if global_util.alive_timer > 6:
                global_util.alive_timer = 0

            global_util.rss_timer += 10

            if global_util.rss_timer >= TIME_RSS_LOOP:
                global_util.rss_timer = 0
                print('rss event')
                for b in bots:  # type: DiscordBot
                    for s in b.local_servers:  # type: Server
                        for r in s.rss:  # type: Feed
                            if r.type == 'twitter':
                                try:
                                    await b.loop.run_in_executor(def_executor, lambda: feeds.scrape_twitter(b, s, r))
                                except Exception as e:
                                    print('Twitter scrape failed with error: {}'.format(e))

                            elif r.type == 'twitch':
                                try:
                                    await feeds.scrape_twitch(b, s, r)
                                except Exception as e:
                                    print('Twitch scrape failed with error: {}'.format(e))

                            elif r.type == 'youtube':
                                try:
                                    await feeds.scrape_youtube(b, s, r)
                                except Exception as e:
                                    print('Youtube scrape failed with error: {}'.format(e))

            global_util.exit_timer += 10
            if global_util.exit_timer >= global_util.TIME_RESPONSE_EXIT and not global_util.save_in_progress:  # kill at 5 min
                exit(1)

            if global_util.internal_shutdown and (not global_util.save_in_progress):
                print('async shutting down...')
                flush_delete_queue()
                asyncio.sleep(2)
                for b in bots:
                    await b.logout()
                break

        except Exception as e:
            print('Async task loop error: {}'.format(e))


bots = BotManager()

# load bots by name into bot manager
with open('globals/bots.json', 'r') as f:
    bot_names = json.load(f)['bots']
    for name in bot_names:
        bots.add(storage.load_bot(name))
    f.close()

# load """cogs""" by startup extensions
for b in bots:  # type: DiscordBot
    b.load_cogs(startup_extensions)


# Full bot loop
# | Create loop, assign tasks, start

loop = asyncio.get_event_loop()

bots.run_all(loop)

loop.create_task(twitch.initialize())  # async library requires init
loop.create_task(delete_messages())

try:
    loop.run_until_complete(background_async())
except Exception:
    for b in bots:  # type: DiscordBot
        loop.run_until_complete(b.logout())
finally:
    try:
        loop.close()
    except Exception:
        exit(5)

if global_util.internal_shutdown:
    exit(5)
exit(1)
