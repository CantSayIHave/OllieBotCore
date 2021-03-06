from util.containers import HelpForm as form

boop = form('`{0}boop [url]`\n'
            '`{0}boop (embed image)`\n'
            '`{0}boop [emoji]`\n'
            '`{0}boop ["pfp"/"avatar"] [optional:@user]`\n'
            'Boops an image.\n'
            'Examples:\n'
            '`{0}boop` (with embedded image)\n'
            '`{0}boop 😳`\n'
            '`{0}boop avatar`')

boop.add_tagline('boop someone or something')


color = form('`{0}color [hex]`\n'
             '`{0}color [red] [green] [blue]`\n'
             'Displays a sample of the requested color.\n'
             '`[hex]` may be formatted as a 1-6 digit hexadecimal\n'
             'number beginning with prefixes `0x` or `#`.\n'
             '`red`, `[green]` and `[blue]` should each be an\n'
             'integer from 0-255.\n'
             '*Examples:*\n'
             '`{0}color #ffaa00`\n'
             '`{0}color 255 170 0`')

color.add_tagline('generate a color sample')


eight_ball = form('`{0}eightball [query]`\n'
                  'Ask the eight ball something.')

eight_ball.add_tagline('ask the eight ball something')


ishihara = form('`{0}ishihara solve [image]`\n'
                'Solves ishihara colorblind tests.\n'
                'You may provide the image in any way you like.')

ishihara.add_tagline('solve colorblind tests')


pick = form('`{0}pick [option1] [option2] [optionN]...`\n'
            '`{0}pick [option1],[option2],[optionN]...`\n'
            'Picks an option.')

pick.add_tagline('pick an option')


poll = form('`{0}poll name=[name] option=[option] option=[option] ...`\n'
            'Creates a poll operated using reactions. Format polls like so:\n'
            '`{0}poll name="Best animal" option=cats option=dogs`\n'
            'For each argument, you only need quotes if there is a space present.\n'
            'You may add up to ten options.')

poll.add_tagline('create a reaction-based poll')


react = form('`{0}react <id> [message ID] [text]`\n'
             '`{0}react <user> [@mention] [message #] [text]`\n'
             '`{0}react <recent> [message #] [text]`\n'
             'Make bigtext reactions to messages. Alternate \n'
             'emoji for most characters exist, but try to limit\n'
             'multiple occurrences of each character.')

react.add_tagline('automates text reactions to messages')


roll = form('`{0}roll <[N]dN> [+/- N] [adv/dis]`\n'
            'Examples:\n'
            '`{0}roll d6`\n'
            '`{0}roll 10d10 +5`\n'
            '`{0}roll d20 -3 dis`')

roll.add_tagline('roll multi-sided dice')


strawpoll = form('`{0}strawpoll [title] [option1] [option2] [optionN]...`\n'
                 'Creates a strawpoll.me poll based on arguments given.\n'
                 'Each poll must have a title and at least two options.\n'
                 'To include spaces, wrap arguments in quotes.\n'
                 '*Examples:*\n'
                 '`{0}strawpoll "best animal" dog cat`\n'
                 '`{0}strawpoll Choose mm/dd/yyyy dd/mm/yyyy yyyy/mm/dd`\n'
                 '(The correct choice is yyyy/mm/dd)')

strawpoll.add_tagline('create a strawpoll.me poll')


timein = form("`{0}timein [location]`\n"
              "Get the current time in a location. Format `location` as an "
              "address, city, state, etc. Example:\n"
              "`{0}timein London`")

timein.add_tagline('get the time in any location')


think = form('`{0}think [url]`\n'
             '`{0}think (embed image)`\n'
             '`{0}think [emoji]`\n'
             '`{0}think ["pfp"/"avatar"] [optional:@user]`\n'
             'Makes an image think.\n'
             'Examples:\n'
             '`{0}think` (with embedded image)\n'
             '`{0}think 🍎`\n'
             '`{0}think pfp`')

think.add_tagline('make someone or something think')


wiki = form('`{}wiki [thing]`\n'
            'Search wikipedia for something')

wiki.add_tagline('search wikipedia for something')
