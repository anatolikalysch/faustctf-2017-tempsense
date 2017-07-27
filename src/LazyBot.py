import random

from textblob import TextBlob

from BotTemplate import Bot
from tech_support import read, DATA_DIR, BadWordException


class CTFBotLazy(Bot):
    def __init__(self):
        self.blacklist = read(DATA_DIR + '111')
        # recognized greetings
        self.key_greeting = read(DATA_DIR + '222')
        # greeting responses
        self.greeting = read(DATA_DIR + '333')
        # if not understood
        self.undefined = read(DATA_DIR + '444')

    def check_for_greeting(self, sentence):
        """If any of the words in the user's input was a greeting, return a greeting response"""
        for word in sentence.words:
            if word.lower() in self.key_greeting:
                return random.choice(self.greeting)

    def process_sentence(self, sentence):
        if sentence in self.key_greeting:
            return random.choice(self.greeting)
        else:
            """Parse the user's inbound sentence and find candidate terms that make up a best-fit response"""
            cleaned = self.preprocess_text(sentence)
            self.filter(cleaned)
            return random.choice(self.undefined)

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
