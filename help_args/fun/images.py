from util.containers import HelpForm as form

bun = form('`{}bun`\n'
           'Fetches a bun 🐇')

bun.add_tagline('summon a bun')


cat = form('`{}cat`\n'
           'Fetches a cat 🐱')

cat.add_tagline('summon a cat')


dropbear = form('`{}dropbear`\n'
                'Fetches a drop bear 🐨')

dropbear.add_tagline('summon a drop bear')


hug = form('`{0}hug`\n'
           '`{0}hug [someone]`\n'
           'Give someone a hug (even yourself!)')

hug.add_tagline('give someone a hug')


pat = form('`{0}pat`\n'
           '`{0}pat [someone]`\n'
           'Give someone a pat (or get one yourself!)')

pat.add_tagline('give someone a pat')


woof = form('`{}woof`\n'
            'Fetches a woof 🐶')

woof.add_tagline('summon a woof')
