from util.containers import HelpForm as form

audioconvert = form('`{}audioconvert [new filetype] [link]`\n'
                    'Converts an audio file to requested filetype.')

imageconvert = form('`{}imgconvert [new filetype] (embed image)`\n'
                    'Converts an image to requested filetype.')

getraw = form('`{0}getraw [message id]`\n'
              '`{0}getraw [channel id] [message id]`\n'
              'Returns the raw string from a message. Useful '
              'to capture `:id:` formatted emoji. If `channel_id` '
              'is not provided, current channel will be used.')

nick_all = form('`{0}nick-all [new name]`\n'
                '`{0}nick-all <reset>`\n'
                'Change the nickname of everyone on the server to '
                '`new name`. Because why not.\n'
                'Using `reset` will remove all nicknames again.')

photoshop = form('`{0}photoshop <mask>`\n'
                 '`{0}photoshop <backgrounds>`\n'
                 '`{0}photoshop <colorreplace>`\n'
                 '`{0}photoshop <capture>`\n'
                 'This module contains an ever-growing suite of photo tools all '
                 'accessible in simple ways. For specific help on each tool, type '
                 '`{0}help photoshop [command]`.\n'
                 'You can also shorten `{0}photoshop` to `{0}ps`.')

photoshop.add_detail(keyword='mask',
                     content='`{0}photoshop mask [mask name] [url/(upload image)]`\n'
                             '`{0}photoshop mask <list>`\n'
                             'Masks one image with another, bases mask foreground on transparency of provided image. '
                             'Currently mask backgrounds are limited, call `list` to get all names. '
                             'Images may be provided however you like.')

photoshop.add_detail(keyword='backgrounds',
                     content='`{0}photoshop backgrounds <add/remove> [name] [url/(upload image)]`\n'
                             '`{0}photoshop backgrounds <list>`\n'
                             'Add, remove, or list mask backgrounds. Images may be provided however you like.')

photoshop.add_detail(keyword='colorreplace',
                     content="`{0}ps <colorreplace/cr> [old color] [new color] [image url/emoji/'capture']`\n"
                             "`{0}ps <colorreplace/cr> [old color] [new color] <pfp> [optional:@member]`\n"
                             "`{0}ps <colorreplace/cr> [old color] [new color] (embed image)`\n"
                             "Replaces one color with another in selected image.\n"
                             "*Note: transparency is ignored.*\n"
                             "__Examples:__\n"
                             "`{0}ps colorreplace ff0000 00ff00 ❤`\n"
                             "`{0}ps cr #000000 #ffaa00 capture`\n"
                             "`{0}ps cr ffffff 000000 (embed image)`")

photoshop.add_detail(keyword='capture',
                     content='`{0}ps capture [number]`\n'
                             'Capture is a photoshop module command that '
                             'allows the capture of an image for use in any '
                             'photoshop command, much like a clipboard. '
                             'Images able to be captured '
                             'are any embedded, uploaded or otherwise linked '
                             'in the last 100 messages for each channel. Once '
                             'an image is captured, it is globally stored. You '
                             'may use it with name `capture` in any photoshop '
                             'command.\n\n'
                             'The argument `number` is the image number in the '
                             'channel, counting up from most recent as 1.')
