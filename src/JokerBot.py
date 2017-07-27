import random

from BotTemplate import Bot
from tech_support import read, DATA_DIR, BadWordException


class CTFBotJoker(Bot):
    def __init__(self):
        self.blacklist = read(DATA_DIR + '11')
        # recognized greetings
        self.key_greeting = read(DATA_DIR + '22')
        # greeting responses
        self.greeting = read(DATA_DIR + '33')
        # if not understood
        self.undefined = read(DATA_DIR + '44')

    def check_for_greeting(self, sentence):
        """If any of the words in the user's input was a greeting, return a greeting response"""
        for word in sentence.words:
            if word.lower() in self.key_greeting:
                return random.choice(self.greeting)

    def process_sentence(self, sentence):
        if sentence in self.key_greeting:
            return random.choice(self.greeting)
        else:
            cleaned = self.preprocess_text(sentence)
            self.filter(cleaned)
            return self.resp_builder()


    def filter(self, resp):
        """Don't allow any words to match our filter list"""
        tokenized = resp.split(' ')
        for word in tokenized:
            if '@' in word or '#' in word or '!' in word:
                raise BadWordException()
            for s in self.blacklist:
                if word.lower().startswith(s):
                    raise BadWordException()


    def preprocess_text(self, sentence):
        """Handle some weird edge cases in parsing, like 'i' needing to be capitalized
        to be correctly identified as a pronoun"""
        cleaned = []
        words = sentence.strip(',;:-').rstrip('\n.!?').split(' ')
        for w in words:
            if w == 'i':
                w = 'I'
            if w == "i'm":
                w = "I'm"
            cleaned.append(w)

        return ' '.join(cleaned)

    def resp_builder(self):
        return 'I don\'t really like support so here\'s a joke instead:\n{}'.format(random.choice(self.undefined))
