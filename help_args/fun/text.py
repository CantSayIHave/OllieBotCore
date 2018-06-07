from util.containers import HelpForm as form

b_ify = form('`{0}b-ify [text]`\n'
             'Adds some 🅱 to text.')

bigtext = form("`{0}bigtext ['-r'] [text]`\n"
               "Converts `text` into regional indicators.\n"
               "If optional `-r` is passed before `text`, the *raw* form of the \n"
               "output will be returned so that you may copy and paste it yourself.\n"
               "__Examples:__\n"
               "`{0}bigtext i am not a bot`\n"
               "`{0}bigtext -r i am totally human`")

straya = form('`{0}stray [text]`\n'
              'Translate text into straylian')
