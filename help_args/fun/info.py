from util.containers import HelpForm as form

joined = form('`{}joined [member]`\n'
              'Get a member\'s server join date\n'
              '`member` may be a mention or just a name to search')

joined.add_tagline('find out when someone joined the server')


userinfo = form('`{}userinfo [user]`\n'
                'Get a user\'s information\n'
                '`user` may be a mention or just a name to search')

userinfo.add_tagline('display a user\'s info')
