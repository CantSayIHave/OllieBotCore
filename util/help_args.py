from util.global_util import help_form as form

audioconvert = form('`{}audioconvert [new filetype] [link]`\n'
                    'Converts an audio file to requested filetype.')

clear = form('`{0}clear [message number]`\n'
             'Clears a number of bot messages')

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



pass
