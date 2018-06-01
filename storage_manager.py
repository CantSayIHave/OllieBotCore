import errno
import json
import os

import discordbot
from server import Server
from util import global_util
from util.containers import *

with open('globals/admins.json', 'r') as f:
    admins = json.load(f)


def mkdir_safe(name: str):
    try:
        os.makedirs(name)  # Make name directory
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def mkfile_safe(fp: str, content: str = None):
    try:
        open(fp, 'r')  # Make name directory
    except Exception:
        with open(fp, 'w') as j:
            j.write(content)
            j.close()


mkdir_safe('images')  # attempt to make /images

try:
    with open('images/hugs.json', 'r') as hugs_in:
        try:
            global_util.hug_library = json.load(hugs_in)
        except Exception:
            global_util.hug_library = []
except FileNotFoundError:
    with open('images/hugs.json', 'w') as hugs_out:
        json.dump([], hugs_out)
        hugs_out.close()
        global_util.hug_library = []

try:
    with open('images/pats.json', 'r') as pats_in:
        try:
            global_util.pat_library = json.load(pats_in)
        except Exception:
            global_util.pat_library = []
except FileNotFoundError:
    with open('images/pats.json', 'w') as pats_out:
        json.dump([], pats_out)
        pats_out.close()
        global_util.pat_library = []


def load_bot(bot_name: str):  # -> discordbot.DiscordBot
    with open('bots/{0}/{0}.json'.format(bot_name), 'r') as ff:
        bot_data = json.load(ff)
        server_list = []

        for s_name in bot_data['server_names']:
            with open('bots/{0}/{1}/{1}.json'.format(bot_name, s_name), 'r') as fi:
                server_data = json.load(fi)
                s_id = server_data['id']
                s_cmd_delay = server_data['cmd_delay']
                s_reee = server_data['reee']
                s_rolemods = server_data['rolemods']
                s_block_list = []
                s_spam_list = server_data['spam_list']
                s_join_msg = server_data['join_msg']
                s_join_channel = server_data['join_channel']
                s_leave_channel = server_data.get('leave_channel', None)
                s_music_chat = server_data.get('music_chat', None)

                for com in server_data['block_list']:
                    s_block_list.append(BlockItem(**com))

            with open('bots/{}/{}/mods.json'.format(bot_name, s_name), 'r') as fi:
                server_mods = json.load(fi)
                s_mods = server_mods['server_mods']

            with open('bots/{}/{}/quotes.json'.format(bot_name, s_name), 'r') as fi:
                server_quotes = json.load(fi)
                s_commands = server_quotes['quotes']  # should be a list of dicts

            with open('bots/{}/{}/rss.json'.format(bot_name, s_name), 'r') as fi:
                server_rss = json.load(fi)
                s_rss = []
                for rss in server_rss['rss']:
                    s_rss.append(Feed(**rss))

            with open('bots/{}/{}/music.json'.format(bot_name, s_name), 'r') as fi:
                s_queue = []
                try:
                    server_queue = json.load(fi)
                    s_queue = server_queue['queue']  # should be a list of dicts
                except Exception:
                    pass

                if not s_queue:
                    s_queue = []

            with open('bots/{}/{}/responses.json'.format(bot_name, s_name), 'r') as fi:
                s_responses = json.load(fi)

            server_list.append(Server(name=s_name,
                                      mods=s_mods,
                                      commands=s_commands,
                                      rss=s_rss,
                                      command_delay=s_cmd_delay,
                                      id=s_id,
                                      rolemods=s_rolemods,
                                      block_list=s_block_list,
                                      spam_timers=s_spam_list,
                                      reee_msg=s_reee,
                                      join_msg=s_join_msg,
                                      join_channel=s_join_channel,
                                      responses=s_responses,
                                      queue=s_queue,
                                      music_chat=s_music_chat,
                                      leave_channel=s_leave_channel))  # Server Build

        print('Loaded bot {}'.format(bot_name))
        return discordbot.DiscordBot(name=bot_name,
                          token=bot_data['token'],
                          desc=bot_data['desc'],
                          prefix=bot_data['prefix'],
                          playing_msg=bot_data['playing_msg'],
                          servers=server_list,
                          admins=admins)


@global_util.global_save
def write_admins(admins: list):
    with open('globals/admins.json', 'w') as f:
        json.dump(admins, f)


@global_util.global_save
def write_bot_data(b):
    with open('bots/{0}/{0}.json'.format(b.name), 'w') as f:
        bot_dict = {'token': b.token,
                    'desc': b.desc,
                    'prefix': b.command_prefix,
                    'playing_msg': b.playing_message}

        s_names = []
        for s in b.local_servers:
            s_names.append(s.name)  # Write server names into bot data file

        bot_dict['server_names'] = s_names

        json.dump(bot_dict, f)


@global_util.global_save
def write_music(b, s):
    try:
        os.makedirs('bots/{}/music'.format(b.name))  # Make name directory in bots folder
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    with open('bots/{}/{}/music.json'.format(b.name, s.name), 'w') as fi:
        s_music = {'queue': s.music.list()}

        json.dump(s_music, fi)


@global_util.global_save
def write_hugs():
    with open('images/hugs.json', 'w') as fh:
        json.dump(global_util.hug_library, fh)
        fh.close()


@global_util.global_save
def write_pats():
    with open('images/pats.json', 'w') as fp:
        json.dump(global_util.pat_library, fp)
        fp.close()


@global_util.global_save
def save_backup():
    os.system('cp -r bots backups')
    os.system('cp -r globals backups')


@global_util.global_save
def write_server_data(b, s: Server):
    if b and s:
        with open('bots/{0}/{1}/{1}.json'.format(b.name, s.name), 'w') as fi:
            server_dict = {'id': s.id,
                           'cmd_delay': s.command_delay,
                           'reee': s.reee_message,
                           'rolemods': s.rolemods,
                           'block_list': [x.__dict__ for x in s.block_list],
                           'spam_list': s.spam_timers,
                           'join_msg': s.join_message,
                           'join_channel': s.join_channel,
                           'leave_channel': s.leave_channel,
                           'music_chat': s.music_chat}

            json.dump(server_dict, fi)

        with open('bots/{}/{}/mods.json'.format(b.name, s.name), 'w') as fi:
            s_mods = {'server_mods': s.mods}

            json.dump(s_mods, fi)

        with open('bots/{}/{}/quotes.json'.format(b.name, s.name), 'w') as fi:
            s_quotes = {'quotes': s.commands}

            json.dump(s_quotes, fi)

        with open('bots/{}/{}/rss.json'.format(b.name, s.name), 'w') as fi:
            s_rss = {'rss': [x.__dict__ for x in s.rss]}

            json.dump(s_rss, fi)

        with open('bots/{}/{}/responses.json'.format(b.name, s.name), 'w') as fi:
            s_responses = [x.__dict__ for x in s.response_lib.responses]

            json.dump(s_responses, fi)

        with open('bots/{}/{}/music.json'.format(b.name, s.name), 'w') as fi:
            s_music = {'queue': list(s.music)}

            json.dump(s_music, fi)


@global_util.global_save
def write_responses(b, s: Server):
    with open('bots/{}/{}/responses.json'.format(b.name, s.name), 'w') as fi:
        s_responses = [x.__dict__ for x in s.response_lib.responses]

        json.dump(s_responses, fi)


# Writes a bot to file
def write_bot(b):
    try:
        os.makedirs('bots/{}'.format(b.name))  # Make name directory in bots folder
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    with open('bots/{0}/{0}.json'.format(b.name), 'w') as f:

        bot_dict = {'token': b.token,
                    'desc': b.desc,
                    'prefix': b.command_prefix,
                    'playing_msg': b.playing_message}

        s_names = []
        for s in b.local_servers:
            s_names.append(s.name)  # Write server names into bot data file

        bot_dict['server_names'] = s_names

        json.dump(bot_dict, f)

    for s in b.local_servers:  # type: Server
        try:
            os.makedirs('bots/{}/{}'.format(b.name, s.name))  # Make server name directory in bots folder
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with open('bots/{0}/{1}/{1}.json'.format(b.name, s.name), 'w') as fi:

            server_dict = {'id': s.id,
                           'cmd_delay': s.command_delay,
                           'reee': s.reee_message,
                           'rolemods': s.rolemods,
                           'block_list': [x.__dict__ for x in s.block_list],
                           'spam_list': s.spam_timers,
                           'join_msg': s.join_message,
                           'join_channel': s.join_channel,
                           'leave_channel': s.leave_channel,
                           'music_chat': s.music_chat}

            json.dump(server_dict, fi)

        with open('bots/{}/{}/mods.json'.format(b.name, s.name), 'w') as fi:
            s_mods = {'server_mods': s.mods}

            json.dump(s_mods, fi)

        with open('bots/{}/{}/quotes.json'.format(b.name, s.name), 'w') as fi:
            s_quotes = {'quotes': s.commands}

            json.dump(s_quotes, fi)

        with open('bots/{}/{}/rss.json'.format(b.name, s.name), 'w') as fi:
            s_rss = {'rss': [x.__dict__ for x in s.rss]}

            json.dump(s_rss, fi)

        with open('bots/{}/{}/responses.json'.format(b.name, s.name), 'w') as fi:
            s_responses = [x.__dict__ for x in s.response_lib.responses]

            json.dump(s_responses, fi)

        with open('bots/{}/{}/music.json'.format(b.name, s.name), 'w') as fi:
            s_music = {'queue': list(s.music)}

            json.dump(s_music, fi)


@global_util.global_save
def write_bot_names(bots: list):
    with open('globals/bots.json', 'w') as f:  # IMPORTANT: writes bot names into bots.json* in globals
        names = [x.name for x in bots]

        bots_dict = {'bots': names}

        json.dump(bots_dict, f)


@global_util.global_save
def write_rss(b, s):
    if b and s:
        with open('bots/{}/{}/rss.json'.format(b.name, s.name), 'w') as fi:
            s_rss = {'rss': [x.__dict__ for x in s.rss]}

            json.dump(s_rss, fi)