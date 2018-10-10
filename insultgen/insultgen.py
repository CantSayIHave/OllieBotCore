import random 
import os
import json

insults = json.load(open(os.path.dirname(__file__) + '/insults.json', 'r'))

pref = 'Thou'


def generate():
    return '{} {} {} {}'.format(pref,
                                random.choice(insults['column1']),
                                random.choice(insults['column2']),
                                random.choice(insults['column3']))
