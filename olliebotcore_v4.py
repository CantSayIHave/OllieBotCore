import asyncio
import logging
from logging.handlers import RotatingFileHandler
import discord

import storage_manager_v2 as storage
# from cogs import feeds
from server import Server
from util import global_util
from util.global_util import *
import util.scheduler as scheduler

import config

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

logger = logging.getLogger()  # discord
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(filename='logs/discord.log', encoding='utf-8', mode='w', maxBytes=10000, backupCount=10)
handler.setFormatter(logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s:%(name)s - %(message)s'))
logger.addHandler(handler)

random.seed()

async_exit_timer = 0

# removed feeds for now
startup_extensions = ["server_utils", "fun", "responses", "music", "think", "sense", "help", "photoshop", "admin"]

startup_extensions = ['cogs.{}'.format(x) for x in startup_extensions]


storage.initialize(config.BOT_NAME)
bot = storage.load_bot()
print('Loaded bot {}'.format(bot.name))

global_util.hug_library = storage.load_hugs()
global_util.pat_library = storage.load_pats()


async def handle_queues():
    while True:
        await asyncio.sleep(1)

        # |-----------[ Message Delete Queue ]-----------|
        for d in global_util.delete_queue:  # type: DeleteMessage
            d.timer -= 1
            if d.timer <= 0:
                try:
                    await d.bot.delete_message(d.message)
                except Exception:
                    print('Failed to delete a message.')
                global_util.delete_queue.remove(d)

        # |-----------[ Scheduled Coroutine Executor ]-----------|
        for c in global_util.coro_queue:  # type: TimedFuture
            c.timer -= 1
            if c.timer <= 0:
                try:
                    await c.coro
                except Exception as e:
                    print('Coro out failed at: {}'.format(e))
                global_util.coro_queue.remove(c)

        # |-----------[ Threadsafe Proxy Message Sending ]-----------|
        while len(global_util.out_messages) > 0:
            try:
                msg_out = global_util.out_messages.popleft()  # type: ProxyMessage
                if msg_out.embed is None:
                    await msg_out.bot.send_message(msg_out.channel, msg_out.content)
                else:
                    await msg_out.bot.send_message(msg_out.channel, em=msg_out.embed)
            except Exception as e:
                print('Proxy sender failed at {}'.format(e))


async def background_async():
    global loop
    while True:
        await asyncio.sleep(10)

        try:
            # |-----------[ Decrement Spam Timers ]-----------|
            for server in bot.local_servers:  # type: Server
                for c in server.spam_timers:
                    if server.spam_timers[c] > 0:
                        server.spam_timers[c] -= 10

                server.response_lib.dec_spam_timers(10)

            # |-----------[ Console Updates ]-----------|
            print('Alive {}'.format(global_util.alive_timer))

            global_util.alive_timer += 1
            if global_util.alive_timer > 6:
                global_util.alive_timer = 0

            # someday I will do this right
            """
            # |-----------[ Update Rss Feeds ]-----------|
            global_util.rss_timer += 10

            if global_util.rss_timer >= TIME_RSS_LOOP:
                global_util.rss_timer = 0
                print('rss event')

                for server in bot.local_servers:  # type: Server
                    if server.feeds:
                        updated_feeds = await olliebot_api.update_feeds(server.feeds)

                        if updated_feeds:
                            await bot.send_message('338508402689048587', '<@305407800778162178> updating {} feeds'
                                                                         ''.format(len(updated_feeds)))

                        # push feed updates
                        for u_feed in updated_feeds:
                            await feeds.send_update(bot, server, u_feed)

                        new_feeds = [x for x in server.feeds if x.first_time is True]

                        # push new feeds
                        for n_feed in new_feeds:
                            await feeds.send_first_update(bot, server, n_feed)

                        storage.write_feeds(server)"""

            # |-----------[ Last Resort Restart ]-----------|
            global_util.exit_timer += 10
            if global_util.exit_timer >= global_util.TIME_RESPONSE_EXIT and not storage.save_in_progress:  # kill at 5 min
                exit(1)

            # |-----------[ Graceful Shutdown ]-----------|
            if global_util.internal_shutdown and (not storage.save_in_progress):
                print('async shutting down...')
                flush_delete_queue()
                await asyncio.sleep(2)
                await bot.logout()
                break

        except Exception as e:
            logging.exception("Background Async error - {}".format(e))


bot.load_cogs(startup_extensions)


# Full bot loop
# | Create loop, assign tasks, start

loop = asyncio.get_event_loop()

loop.create_task(bot.start(bot.token))

# loop.create_task(twitch.initialize())  # async library requires init
loop.create_task(handle_queues())
loop.create_task(scheduler.task_loop())  # datetime callback scheduling

try:
    loop.run_until_complete(background_async())
except:
    loop.run_until_complete(bot.logout())
finally:
    try:
        loop.close()
    except:
        exit(5)

# an error code 5 tells the bootstrapper not to restart
if global_util.internal_shutdown:
    exit(5)
exit(1)
