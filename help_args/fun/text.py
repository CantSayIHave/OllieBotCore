from util.containers import HelpForm as form

b_ify = form('`{0}b-ify [text]`\n'
             'Adds some 🅱 to text.')

b_ify.add_tagline('add some 🅱️ to text')


bigtext = form("`{0}bigtext ['-r'] [text]`\n"
               "Converts `text` into regional indicators.\n"
               "If optional `-r` is passed before `text`, the *raw* form of the \n"
               "output will be returned so that you may copy and paste it yourself.\n"
               "__Examples:__\n"
               "`{0}bigtext i am not a bot`\n"
               "`{0}bigtext -r i am totally human`")

bigtext.add_tagline('transform text into regional indicators')


straya = form('`{0}stray [text]`\n'
              'Translate text into straylian')

straya.add_tagline('make text straylian')
