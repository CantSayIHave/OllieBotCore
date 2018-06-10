from util.containers import HelpForm as form

clear = form('`{0}clear [message number]`\n'
             'Clears a number of bot messages')

clear.add_tagline('clear a number of bot messages')
clear.high_perm = True


playing = form('`{0}playing [thing]`\n'
               "Changes bot's `playing` status\n"
               'Argument does not need quotes\n'
               'Example: `{0}playing with carrots`')

playing.add_tagline('change the bot\'s `playing` status')
playing.high_perm = True


presence = form('`{0}presence [type] [value]`\n'
                "Changes bot's presence, ie `playing`\n"
                '`type` can be `playing`, `streaming`, or `listening`\n'
                'Example: `{0}presence playing with carrots`')

presence.add_tagline('change the bot\'s presence')
presence.high_perm = True
