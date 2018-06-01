from util.global_util import help_form as form


b_ify = form('`{0}b-ify [text]`\n'
             'Adds some 🅱 to text.')

bigtext = form("`{0}bigtext ['-r'] [text]`\n"
                                            "Converts `text` into regional indicators.\n"
                                            "If optional `-r` is passed before `text`, the *raw* form of the \n"
                                            "output will be returned so that you may copy and paste it yourself.\n"
                                            "__Examples:__\n"
                                            "`{0}bigtext i am not a bot`\n"
                                            "`{0}bigtext -r i am totally human`")

bun = form('`{}bun`\n'
           'Fetches a bun 🐇')

cat = form('`{}cat`\n'
           'Fetches a cat 🐱')



reee = form("Set reee on/off: `{0}reee <true/false>`\n"
                                                                "Get reee state: `{0}reee`\n"
                                                                'Set reee response: `{0}reee <response> [response]`\n'
                                                                'Get reee response: `{0}reee <response>`')



pass

