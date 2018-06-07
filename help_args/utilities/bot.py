from util.containers import HelpForm as form

clear = form('`{0}clear [message number]`\n'
             'Clears a number of bot messages')

playing = form('`{0}playing [thing]`\n'
               "Changes bot's `playing` status\n"
               'Argument does not need quotes\n'
               'Example: `{0}playing with carrots`')

presence = form('`{0}presence [type] [value]`\n'
                "Changes bot's presence, ie `playing`\n"
                '`type` can be `playing`, `streaming`, or `listening`\n'
                'Example: `{0}presence playing with carrots`')
