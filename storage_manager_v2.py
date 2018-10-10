"""

The MIT License (MIT)

Copyright (c) 2018 CantSayIHave

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

---------------------------------------------------------------------------

storage module for bot storage

Uses MongoDB for all storage operations

Assumes a structure like so:
[ Database: Bot Name ]
 |
 |-[ Collection: Admin ]
    |
    |-[ Document: Bot Info ]
    |-[ Document: Admin List ]
 |
 |-[ Collection: Resources ]
    |
    |-[ Document: image urls/sticker profiles/etc ]
 |
 |
 |-[ Collection: User Data ]
    |
    |-[ Document: User ]
 |
 |-[ Collection: ServerN ]
    |
    |-[ Document: Server Info ]
    |-[ Document: Mod List ]
    |-[ Document: Responses ]
    |-[ Document: Feeds ]
    |-[ Document: Birthdays ]
    |-[ Document: etc ]

Bot-level structures are assumed to exist. Server data will be
created if it does not exist.

All documents must have a '__docname__' attribute for id.
Documents storing a single (key, value) other than a `__docname__`
and a mongo-`_id` will assume that single key is called 'data'.

For example:

The 'admins' document in the 'admin' collection is structured like so:
{
    "_id": xxx,
    "__docname__": "admins",
    "data": [a, list, of, admins]
}

"""
import json

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

import discordbot
from server import Server
from util import global_util, command_util, exceptions
from util.containers import *
from util.feeds import *

"""-------------------------------- Mongo Initialization --------------------------------"""

mongo_client = None

try:
    mongo_client = MongoClient()
except Exception as e:
    raise exceptions.BotInitializeError('Critical exception on storage initialization:{}'.format(e))

# actual database - represents all bot data
database = None  # type: Database

bot_name = None  # type: str

# default collections
admin = None  # type: Collection
resources = None  # type: Collection
users = None  # type: Collection


def initialize(_bot_name: str):
    """
    Initialize database pointers to a bot

    :param _bot_name: name of bot
    :return:
    """
    global database, bot_name, admin, resources, users
    database = mongo_client[_bot_name]
    bot_name = _bot_name
    admin = database.admin
    resources = database.resources
    users = database.users


"""-------------------------------- Safe Saving --------------------------------"""

save_in_progress = False


def global_save(func):
    """
    Decorator to ensure planned `exit()`s do not occur during a save
    """

    def decor(*args, **kwargs):
        global save_in_progress
        save_in_progress = True
        func(*args, **kwargs)
        save_in_progress = False

    return decor


"""-------------------------------- Serialization --------------------------------"""


# anonymous object for storage
class GenericStorage:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


# for serializing complex objects
def serialize(obj):
    if isinstance(obj, discord.User):
        return GenericStorage(username=obj.name,
                              id=obj.id,
                              discriminator=obj.discriminator,
                              avatar=obj.avatar,
                              bot=obj.bot).__dict__
    if isinstance(obj, Birthday):
        return GenericStorage(user=serialize(obj.user), dt=obj.dt.strftime(global_util.DATETIME_FORMAT)).__dict__


def deserialize(obj: dict, baseclass):
    if baseclass is Birthday:
        return Birthday(user=deserialize(obj['user'], discord.User),
                        dt=datetime.strptime(obj['dt'], global_util.DATETIME_FORMAT))
    elif baseclass is discord.User:
        return baseclass(**obj)


"""-------------------------------- Mongo Utils --------------------------------
    
    Method
    ------
    Document storage is broken into two types: documents and simple documents.
    
    Each stores a '__docname__' attribute marking document name. A regular document
    will also store several (key:value) pairs, but a simple document assumes data
    whose key is the docname and stores data under the standard key 'data'.
    
    Document
    --------
    {
        '_id': 0,
        '__docname__': 'bot_data',
        'name': 'OllieBot',
        'prefix': '.',
        'etc': 'etc
    }
    
    Simple Document
    ---------------
    {
        '_id': 1,
        '__docname__': 'admins',
        'data': ['a', 'list', 'of', 'admins']
    }

"""


def update_simple_document(collection: Collection, docname: str, data):
    if collection.find_one(filter={'__docname__': docname}):
        collection.update_one(filter={'__docname__': docname},
                              update={'$set': {'data': data}})
    else:
        collection.insert_one({'__docname__': docname,
                               'data': data})


def update_document(collection: Collection, docname: str, **data):
    if collection.find_one(filter={'__docname__': docname}):
        collection.update_one(filter={'__docname__': docname},
                              update={'$set': data})
    else:
        data['__docname__'] = docname
        collection.insert_one(data)


def get_simple_document(collection: Collection, docname: str):
    doc = collection.find_one(filter={'__docname__': docname})
    if doc:
        return doc['data']


def get_document(collection: Collection, docname: str) -> dict:
    return collection.find_one(filter={'__docname__': docname})


def get_server_collection(server: Server = None, id: str = None) -> Collection:
    """Retrieve a server's collection, creates if it does not exist"""
    if id:
        return database['server_{}'.format(id)]
    return database['server_{}'.format(server.id)]


"""-------------------------------- Loading --------------------------------"""


def load_bot() -> discordbot.DiscordBot:
    """Loads the bot

    Returns
    -------
    :class:`discordbot.DiscordBot`
        the deserialized bot

    Method
    ------
    Check initialization,
    Get bot data,
    For each server:
        deserialize server,
        add to server list,
    Get admins,
    Return bot
    """
    if not database:
        raise exceptions.StorageError('Storage has not been initialized')

    bot_data = get_document(admin, docname='bot_data')

    server_list = []

    for s_id in bot_data['server_ids']:

        s_id = str(s_id)  # reformat all server ids as strings silly

        s_collection = get_server_collection(id=s_id)

        server_data = get_document(s_collection, docname='server_data')

        s_name = server_data['name']
        s_spam_time = server_data['spam_time']
        s_reee_message = server_data['reee_message']
        s_mods = server_data['mods']
        s_rolemods = server_data['rolemods']
        s_spam_list = server_data['spam_list']
        s_join_msg = server_data['join_msg']
        s_join_channel = server_data['join_channel']
        s_leave_channel = server_data.get('leave_channel', None)
        s_bind_chat = server_data.get('bind_chat', None)
        s_default_role = server_data.get('default_role', None)

        s_block_list = [BlockItem(**command) for command in server_data['block_list']]

        s_feeds = [build_feed(f) for f in get_simple_document(s_collection, docname='feeds')]

        s_music_queue = get_simple_document(s_collection, docname='music_queue')

        s_responses = get_simple_document(s_collection, docname='responses')

        s_birthdays = [deserialize(x, Birthday) for x in get_simple_document(s_collection, docname='birthdays')]

        server_list.append(Server(name=s_name,
                                  mods=s_mods,
                                  feeds=s_feeds,
                                  command_delay=s_spam_time,
                                  id=s_id,
                                  rolemods=s_rolemods,
                                  block_list=s_block_list,
                                  spam_timers=s_spam_list,
                                  reee_message=s_reee_message,
                                  join_msg=s_join_msg,
                                  join_channel=s_join_channel,
                                  responses=s_responses,
                                  music_queue=s_music_queue,
                                  bind_chat=s_bind_chat,
                                  leave_channel=s_leave_channel,
                                  birthdays=s_birthdays,
                                  default_role=s_default_role))  # Server Build

    admins = admin.find_one({'__docname__': 'admins'})['data']

    return discordbot.DiscordBot(name=bot_name,
                                 token=bot_data['token'],
                                 desc=bot_data['desc'],
                                 prefix=bot_data['prefix'],
                                 playing_message=bot_data['playing_message'],
                                 local_servers=server_list,
                                 admins=admins)


"""-------------------------------- Admin Saving --------------------------------

    Method
    ------
    Admin collections consist of one document named [ 'bot_data' ] which stores:
        `token`
        `desc`
        `prefix`
        `playing_message`
    
    As well as one simple document storing the data `admins`

"""


# target: admin.admins
@global_save
def write_admins(admins: list):
    """Writes admin list to database

    Parameters
    ----------
    admins: list
        list of admin ids, currently as strings

    """
    update_simple_document(collection=admin,
                           docname='admins',
                           data=admins)


# target: admin.bot_data
@global_save
def write_bot_data(bot: discordbot.DiscordBot):
    """Writes bot data to database

    Note: this only writes bot metadata, not server data

    Parameters
    ----------
    bot: :class:`discordbot.DiscordBot`

    """
    bot_dict = {'token': bot.token,
                'desc': bot.desc,
                'prefix': bot.command_prefix,
                'playing_message': bot.playing_message}

    server_ids = [str(s.id) for s in bot.local_servers]

    bot_dict['server_ids'] = server_ids

    update_document(collection=admin,
                    docname='bot_data',
                    **bot_dict)


"""-------------------------------- Server Saving --------------------------------

    Method
    ------
    Server collections consist of one document called [ 'server_data' ] for the following data:
        `name`
        `spam_time`
        `reee`
        `mods`
        `rolemods`
        `block_list`
        `spam_list`
        `join_msg`
        `join_channel`
        `leave_channel`
        `bind_chat`

    As well as one simple document for each of the following data:
        `music_queue`
        `feeds`
        `responses`
        `birthdays`
    
    Each standalone method may take the server collection to save retrieval time,
    else it will get the collection from the provided server
    
    Server collections are named by the format [ 'server_{id}' ]
    
    The :method:`write_server` function combines all standalone methods

"""


# todo: create server if no exist


# target: server.music
@global_save
def write_music(server: Server, s_collection: Collection = None):
    """Writes a server's music queue to database

    Parameters
    ----------
    server: Server
        the server instance
    s_collection: Collection
        (optional) the server collection to write to

    """
    if not s_collection:
        s_collection = get_server_collection(server)

    update_simple_document(collection=s_collection,
                           docname='music_queue',
                           data=server.music.list())


# target: server.feeds
@global_save
def write_feeds(server: Server, s_collection: Collection = None):
    """Writes a server's rss feeds to database

    Parameters
    ----------
    server: Server
        the server instance
    s_collection: Collection
        (optional) the server collection to write to

    """
    if not s_collection:
        s_collection = get_server_collection(server)

    update_simple_document(s_collection,
                           docname='feeds',
                           data=[x.as_dict() for x in server.feeds])


# target: server.responses
@global_save
def write_responses(server: Server, s_collection: Collection = None):
    """Writes a server's responses to database

    Parameters
    ----------
    server: Server
        the server instance
    s_collection: Collection
        (optional) the server collection to write to

    """
    if not s_collection:
        s_collection = get_server_collection(server)

    update_simple_document(s_collection,
                           docname='responses',
                           data=server.response_lib.as_list())


# target: server.birthdays
@global_save
def write_birthdays(server: Server, s_collection: Collection = None):
    """Writes a server's birthdays to database

    Parameters
    ----------
    server: Server
        the server instance
    s_collection: Collection
        (optional) the server collection to write to

    """
    if not s_collection:
        s_collection = get_server_collection(server)

    update_simple_document(s_collection,
                           docname='birthdays',
                           data=[serialize(x) for x in server.birthdays])


@global_save
def write_server_data(server: Server, s_collection: Collection = None):
    """Writes a server's "server data" to database

    Parameters
    ----------
    server: Server
        the server instance
    s_collection: Collection
        (optional) the server collection to write to

    """
    if not s_collection:
        s_collection = get_server_collection(server)

    server_dict = {'name': server.name,
                   'spam_time': server.spam_time,
                   'reee_message': server.reee_message,
                   'mods': server.mods,
                   'rolemods': server.rolemods,
                   'block_list': [x.__dict__ for x in server.block_list],
                   'spam_list': server.spam_timers,
                   'join_msg': server.join_message,
                   'join_channel': server.join_channel,
                   'leave_channel': server.leave_channel,
                   'bind_chat': server.music.bind_chat,
                   'default_role': server.default_role}

    update_document(s_collection,
                    docname='server_data',
                    **server_dict)


@global_save
def write_server(server: Server):
    """Writes a server to the database

    Parameters
    ----------
    server: Server
        The server instance to serialize

    """
    s_collection = get_server_collection(server)

    write_server_data(server, s_collection)

    write_feeds(server, s_collection)

    write_responses(server, s_collection)

    write_music(server, s_collection)

    write_birthdays(server, s_collection)


"""-------------------------------- Resources Saving --------------------------------"""


# target: resources.hugs
@global_save
def write_hugs():
    """Writes the hug library to database"""
    update_simple_document(resources, docname='hugs', data=global_util.hug_library)


# target: resources.pats
@global_save
def write_pats():
    """Writes the pat library to database"""
    update_simple_document(resources, docname='pats', data=global_util.pat_library)


# target: resources.photoshop
@global_save
def write_backgrounds(backgrounds: dict):
    """Writes background list (a bunch of urls)"""
    update_document(resources, docname='photoshop', backgrounds=backgrounds)


# target: resources.stickers
@global_save
def write_stickers(stickers: dict):
    update_simple_document(resources, docname='stickers', data=stickers)

"""-------------------------------- Resources Loading --------------------------------"""


# source: resources.hugs
def load_hugs() -> list:
    return get_simple_document(resources, docname='hugs')


# source: resources.pats
def load_pats() -> list:
    return get_simple_document(resources, docname='pats')


# source: resources.photoshop
def load_backgrounds() -> dict:
    return get_document(resources, docname='photoshop')['backgrounds']


# source: resources.stickers
def load_stickers() -> dict:
    return get_simple_document(resources, docname='stickers')


def ghetto_write_server(path: str, server_name: str):
    with open('{}/{}/{}.json'.format(path, server_name, server_name), 'r') as file:
        server_data = json.load(file)

    with open('{}/{}/mods.json'.format(path, server_name), 'r') as file:
        server_mods = json.load(file)['server_mods']

    s_rss = []

    with open('{}/{}/music.json'.format(path, server_name), 'r') as fi:
        s_queue = []
        try:
            server_queue = json.load(fi)
            s_queue = server_queue['queue']  # should be a list of dicts
        except Exception:
            pass

        if not s_queue:
            s_queue = []

    with open('{}/{}/responses.json'.format(path, server_name), 'r') as fi:
        s_responses = json.load(fi)

    s_birthdays = []
    if global_util.file_exists('{}/{}/birthdays.json'.format(path, server_name)):
        with open('{}/{}/birthdays.json'.format(path, server_name), 'r') as fi:
            raw_birthdays = json.load(fi)
            s_birthdays = [deserialize(x, Birthday) for x in raw_birthdays]

    s_id = server_data['id']
    s_cmd_delay = server_data['cmd_delay']
    s_reee = server_data['reee']
    s_rolemods = server_data['rolemods']
    s_spam_list = server_data['spam_list']
    s_block_list = [BlockItem(**command) for command in server_data['block_list']]
    s_join_msg = server_data['join_msg']
    s_join_channel = server_data['join_channel']
    s_leave_channel = server_data.get('leave_channel', None)
    s_music_chat = server_data.get('music_chat', None)
    s_default_role = server_data.get('default_role', None)

    s_collection = get_server_collection(id=s_id)

    server_dict = {'name': server_name,
                   'spam_time': s_cmd_delay,
                   'reee_message': s_reee,
                   'mods': server_mods,
                   'rolemods': s_rolemods,
                   'block_list': [x.__dict__ for x in s_block_list],
                   'spam_list': s_spam_list,
                   'join_msg': s_join_msg,
                   'join_channel': s_join_channel,
                   'leave_channel': s_leave_channel,
                   'bind_chat': s_music_chat,
                   'default_role': s_default_role}

    update_document(s_collection,
                    docname='server_data',
                    **server_dict)

    update_simple_document(collection=s_collection,
                           docname='music_queue',
                           data=s_queue)

    update_simple_document(s_collection,
                           docname='feeds',
                           data=[x.as_dict() for x in s_rss])

    update_simple_document(s_collection,
                           docname='responses',
                           data=s_responses)

    update_simple_document(s_collection,
                           docname='birthdays',
                           data=[serialize(x) for x in s_birthdays])


def ghetto_write_hugs(filepath: str):
    """Writes the hug library to database"""
    with open(filepath, 'r') as file:
        hug_lib = json.load(file)
    update_simple_document(resources, docname='hugs', data=hug_lib)


# target: resources.pats
def ghetto_write_pats(filepath: str):
    """Writes the pat library to database"""
    with open(filepath, 'r') as file:
        pat_lib = json.load(file)
    update_simple_document(resources, docname='pats', data=pat_lib)


# target: resources.photoshop
def ghetto_write_backgrounds(backgrounds: dict):
    """Writes background list (a bunch of urls)"""
    update_document(resources, docname='photoshop', backgrounds=backgrounds)


# target: resources.stickers
def ghetto_write_stickers(stickers: dict):
    update_simple_document(resources, docname='stickers', data=stickers)


# target: admin.bot_data
def ghetto_write_bot_data(token, desc, prefix, playing, ids: list):
    """Writes bot data to database

    Note: this only writes bot metadata, not server data

    Parameters
    ----------
    bot: :class:`discordbot.DiscordBot`

    """
    bot_dict = {'token': token,
                'desc': desc,
                'prefix': prefix,
                'playing_message': playing,
                'server_ids': ids}

    update_document(collection=admin,
                    docname='bot_data',
                    **bot_dict)
