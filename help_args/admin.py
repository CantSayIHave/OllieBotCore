from util.containers import HelpForm as form


backup = form('`{}backup`\n'
              'Backup all bots to file.')

delet = form('`{}delet [server id] [channel id] [message id]`\n'
             'Do a delet')

invite = form('`{}invite`\n'
              'Returns bot\'s invite link.')

prefix = form('`{0}prefix`\n'
              '`{0}prefix <set> [prefix]`\n'
              'Get or set bot prefix.')

regen = form('`{}regen`\n'
             'Restart bot script.')

repl = form('`{}repl [optional:@member]`\n'
            'Opens a Python REPL. Available args are `ctx` and `member` if passed.')

sayd = form("`{0}sayd [message]`\n"
            "`{0}sayd <embed> [args]`\n"
            "Sayd (say-delete) says a message, then "
            "deletes your command. Args should be space "
            "separated and subargs comma-separated. Use "
            "a `:` to denote the start of an arg. Arg list:\n"
            "`init - title,desc,url,colour`\n"
            "`footer - text,icon_url`\n"
            "`image - url`\n"
            "`thumbnail - url`\n"
            "`author - name,url,icon_url`\n"
            "`field - name,value,inline`\n"
            "Example:\n"
            "```python\n"
            "{0}sayd embed init:title=SampleEmbed,desc=\"a "
            "description\",color=0xff0000 field:name=\"One "
            "field\",value=things field:name=\"Two field\","
            "value=\"more things\",inline=False\n```")

send = form('`{}send [channel id] [text]`\n'
            'Send a message to a channel.')

server = form("`{0}server <add> [(bot name)/'this'] [(invite url)/'this'] ["
              "quote delay]`\n"
              "Note: 'this' refers to bot/server this command is being executed from\n"
              "Example: `{0}server add this this 3` adds current server to current bot with "
              "spam timer of 3 minutes\n"
              "*Note: This command is deprecated, as servers are now added automagically. "
              "It remains for manual control in case of errors, but you shouldn't ever have "
              "to use it*")

serverid = form('`{}serverid`\n'
                'Get the server\'s ID.')

sleep = form('`{}sleep`\n'
             'Shutdown bot script.')

write = form('`{}write`\n'
             'Writes all bots to file.')
