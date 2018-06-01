from util.global_util import help_form as form

b_ify = form('`{0}b-ify [text]`\n'
             'Adds some 🅱 to text.')

bigtext = form("`{0}bigtext ['-r'] [text]`\n"
               "Converts `text` into regional indicators.\n"
               "If optional `-r` is passed before `text`, the *raw* form of the \n"
               "output will be returned so that you may copy and paste it yourself.\n"
               "__Examples:__\n"
               "`{0}bigtext i am not a bot`\n"
               "`{0}bigtext -r i am totally human`")

bun = form('`{}bun`\n'
           'Fetches a bun 🐇')

cat = form('`{}cat`\n'
           'Fetches a cat 🐱')

dropbear = form('`{}dropbear`\n'
                'Fetches a drop bear 🐨')

joined = form('`{}joined [member]`\n'
              'Get a member\'s server join date\n'
              '`member` may be a mention or just a name to search')

playing = form('`{0}playing [thing]`\n'
               "Changes bot's `playing` status\n"
               'Argument does not need quotes\n'
               'Example: `{0}playing with carrots`')

poll = form('`{0}poll name=[name] option=[option] option=[option] ...`\n'
            'Creates a poll operated using reactions. Format polls like so:\n'
            '`{0}poll name="Best animal" option=cats option=dogs`\n'
            'For each argument, you only need quotes if there is a space present.\n'
            'You may add up to ten options.')

presence = form('`{0}presence [type] [value]`\n'
                "Changes bot's presence, ie `playing`\n"
                '`type` can be `playing`, `streaming`, or `listening`\n'
                'Example: `{0}presence playing with carrots`')

reee = form("Set reee on/off: `{0}reee <true/false>`\n"
            "Get reee state: `{0}reee`\n"
            'Set reee response: `{0}reee <response> [response]`\n'
            'Get reee response: `{0}reee <response>`')

react = form('`{0}react <id> [message ID] [text]`\n'
                                                                '`{0}react <user> [@mention] [message #] [text]`\n'
                                                                '`{0}react <recent> [message #] [text]`\n'
                                                                'Make bigtext reactions to messages. Alternate \n'
                                                                'emoji for most characters exist, but try to limit\n'
                                                                'multiple occurrences of each character.')

roll = form('`{0}roll <[N]dN> [+/- N] [adv/dis]`\n'
                                                                'Examples:\n'
                                                                '`{0}roll d6`\n'
                                                                '`{0}roll 10d10 +5`\n'
                                                                '`{0}roll d20 -3 dis`')

strawpoll = form('`{0}strawpoll [title] [option1] [option2] [optionN]...`\n'
                 'Creates a strawpoll ')

timein = form("`{0}timein [location]`\n"
                                   "Get the current time in a location. Format `location` as an "
                                   "address, city, state, etc. Example:\n"
                                   "`{0}timein London`")

userinfo = form('`{}userinfo [user]`\n'
                'Get a user\'s information\n'
                '`user` may be a mention or just a name to search')

wiki = form('`{}wiki [thing]`\n'
            'Search wikipedia for something')

woof = form('`{}woof`\n'
            'Fetches a woof 🐶')

pass
