from util.containers import HelpForm as form

birthday = form('`{0}birthday <add/edit> [@user] [date]`\n'
                '`{0}birthday <remove> [@user]`\n'
                '`{0}birthday <get> [user/date]`\n'
                'Add a birthday for the bot to monitor. Birthday '
                'notifications will be dispatched at 12am PST each date.\n'
                '*Note:* `date` *may be given in any recognizable format*\n'
                'Examples:\n'
                '`{0}birthday add `{1}` july 15`\n'
                '`{0}birthday edit `{1}` tomorrow`\n'
                '`{0}birthday get july 15`')

birthday.add_tagline('manage member birthday notifications')

block = form('`{0}block <all/here> [command]`\n'
             '`{0}block [#channel] [command]`\n'
             '`{0}block <list>`\n'
             'Blocks a specific command from non-mods. You can '
             'block any command, even quotes. \n'
             'Using `all` will block the command server-wide, while '
             '`here` will block in only the channel this is called '
             'from.\n'
             'See `{0}unblock` '
             'to unblock commands')

block.add_tagline('block a command from non-mods')
block.high_perm = True

emotes = form('`{0}emotes <suggest> [link]`\n'
              '`{0}emotes <suggest> (upload image in message)`\n'
              '`{0}emotes <add> <name> [link]`\n'
              '`{0}emotes <add> <name> (upload image in message)`\n'
              '`{0}emotes <list/clear>`\n'
              '*Note: `add`, `list` and `clear` are only visible to and usable by mods\n'
              'This is a method for suggesting emotes to the '
              'moderators and adding custom emoji to the server.\n'
              '`[link]` should be the full web '
              'address to the image. `suggest/add` '
              'may be called without a link as long as an image '
              'is uploaded within the '
              'message')

emotes.add_tagline('suggest and add emotes to the server')
emotes.high_perm = True

leavechannel = form('`{0}leavechannel <set> [#channel]`\n'
                    '`{0}leavechannel <off>`\n'
                    'Set member leave messages to a channel, or turn them off.\n'
                    'Messages are off by default.')

leavechannel.add_tagline('manage member leave announcements')
leavechannel.high_perm = True

mute = form('`{0}mute [@member] [minutes]`\n'
            'Mutes a member for a period of time, default 1 minute.\n'
            'Will attempt to voice mute and assign a role called `timeout` to '
            'selected member, given the permissions to do so.\n'
            'Unmuting will occur when time is up, or by calling `{0}unmute [@member]`.\n'
            'You may create a role called `timeout` and set permissions as you like, or call '
            '`{0}roles timeout` to create a default full-server muting role.')

mute.add_tagline('mute a member for a period of time')
mute.high_perm = True

perm = form("`{0}perm <mod/unmod> [@mention]`\n"
            "`{0}perm <check> <mod> [@mention]`\n"
            '`{0}perm rolemod <add/remove> [@role]`\n'
            '`{0}perm rolemod <check> [@role]`\n'
            '`{0}perm rolemod <list>`\n'
            'Mod, unmod, or check mod status of users. Rolemod '
            'allows modding of an entire role.\n'
            "Example: `{0}perm mod @Olliebot` or `{0}perm check mod @Olliebot`\n"
            "*Note*: make sure [@mention] or [@role] are Discord-formatted blue links, "
            "like {1}")

perm.add_tagline('manage bot-level member permissions')
perm.high_perm = True

purge = form('**Purge usage**:\n'
             '`{0}purge [message number]`\n'
             '`{0}purge [member] [message number:optional]`\n'
             'Clears a number of messages. If `member` is not \n'
             'passed, clearing is indiscriminate.\n'
             'If `message number` is not passed, 10 messages will '
             'be purged.')

purge.add_tagline('purge a number of messages from member(s)')
purge.high_perm = True

reee = form("Set reee on/off: `{0}reee <true/false>`\n"
            "Get reee state: `{0}reee`\n"
            'Set reee response: `{0}reee <response> [response]`\n'
            'Get reee response: `{0}reee <response>`')

reee.add_tagline('manage bot\'s `reee` response')
reee.high_perm = True

roles = form('`{0}roles <add/remove> [base role] [new role] [optional:"NoRole"]`\n'
             '`{0}roles <replace> [old role] [new role]`\n'
             '`{0}roles <create> [name] [color]`\n'
             'The roles command automates mass addition, removal and replacement of roles, '
             'as well as creation for custom colors (for mobile users).'
             'Example:\n'
             '`{0}roles add @SomeRole @OtherRole` will add `@OtherRole` to all users with '
             'role `@SomeRole`\n'
             'If the third argument "NoRole" is passed to `add/remove`, the second role '
             'will be added to/removed from only users with no role\n'
             'In `add/remove`, "base role" is used only to qualify, it will not be '
             'affected.\n'
             '*Note: make sure [base role] and [new role] are discord-formatted '
             'mentions*')

roles.add_tagline('automates mass addition, removal and replacement of roles')
roles.high_perm = True

rss = form("`{0}rss <add/remove> <twitter/twitch/youtube> [username]`\n"
           "`{0}rss <list>`\n"
           "Example: `.rss add twitter @pewdiepie` binds PieDiePie's twitter feed to the "
           "channel this is called from\n "
           "Call `.rss help users` for user formatting info")

rss.add_detail(keyword='users',
               content="For Twitter, use the user's twitter handle, like "
                       "`@Shoe0nHead`\n "
                       "For Twitch, use the username found in the url format "
                       "`www.twitch.tv/[username]`\n "
                       "- *Example:* Chris Ray Gun: `https://www.twitch.tv/nemesiscrm` - use "
                       "`nemesiscrm`\n "
                       "For YouTube, use the username found in the url format "
                       "`https://www.youtube.com/user/[username]`\n"
                       "- *Example:* Phillip DeFranco: `https://www.youtube.com/user/sxephil` - "
                       "use `sxephil`")

rss.add_tagline('manage rss feeds on channels')
rss.high_perm = True

spamtimer = form("`{0}spamtimer`\n"
                 "`{0}spamtimer <set> [minutes]`\n"
                 "`{0}spamtimer <add/remove> [name]`\n"
                 "`{0}spamtimer <list>`\n"
                 "Sets timer for each `quote` or "
                 "add/remove command to spam time")

spamtimer.add_tagline('set the spam timer and commands to time')
spamtimer.high_perm = True

unmute = form('`{0}unmute [@member]`\n'
              'Unmutes a member, both in voice and removing a `timeout` role.')

unmute.add_tagline('unmute a member')
unmute.high_perm = True

userjoin = form("Get user join message: `{0}userjoin <message>`\n"
                "Set user join message: `{0}userjoin <message> [message]`\n"
                "Set user join output channel: `{0}userjoin <channel> [channel]`\n\n"
                "The user join message may be formatted with an `@u` as a placeholder "
                "for the new member.\n"
                "For example: `Welcome to the server, @u!` displays as:\n"
                "Welcome to the server, {1}!\n\n"
                "The channel this message is displayed in defaults to the server's "
                "default channel but may be set with the `<channel>` subcommand, where "
                "`[channel]` is the blue-link mention of the channel.")

userjoin.add_tagline('edit message and channel for member join announcement')
userjoin.high_perm = True
