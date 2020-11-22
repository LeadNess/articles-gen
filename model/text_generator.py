import re
from typing import Generator

from .chain_storage import ChainStorage
from .utils import EncoderStorage, WordsEncoder, TextProcessor


class TextGenerator:
    pg_chain: ChainStorage
    pg_encoder: EncoderStorage
    encoder: WordsEncoder
    model_name: str
    state_size: int
    re_process: re.Pattern = re.compile(r'[^a-zA-Zа-яА-Я ]')

    def __init__(self,
                 pg_chain: ChainStorage,
                 pg_encoder: EncoderStorage,
                 model_name: str,
                 state_size: int,
                 input_text=None):
        self.pg_chain = pg_chain
        self.pg_encoder = pg_encoder
        self.model_name = model_name
        self.state_size = state_size

        if input_text:
            if isinstance(input_text, Generator):
                train_corpus = list(TextProcessor.get_text_gen(input_text))
            else:
                train_corpus = list(TextProcessor.get_text_gen([input_text, ]))

            self.encoder = WordsEncoder()
            encoded_train_corpus = self.encoder.fit_encode(train_corpus)

            self.pg_encoder.add_encoder(model_name, self.encoder)
            self.pg_chain.add_model(model_name, encoded_train_corpus, state_size)
        else:
            self.encoder = self.pg_encoder.load_encoder(model_name)

    def words_split(self, sentence: str) -> list:
        words_list = []
        for word in sentence.split():
            processed_word = self.re_process.sub('', word.lower())
            if processed_word:
                words_list.append(processed_word)
        return words_list

    def words_join(self, words_list: list) -> str:
        return ' '.join(words_list)

    def make_sentence(self, init_state: list, **kwargs):
        tries = kwargs.get('tries', 10)
        max_words = kwargs.get('max_words', None)
        min_words = kwargs.get('min_words', None)

        if init_state is not None:
            init_state = self.encoder.encode_words_list(init_state)
            prefix = init_state
            for word in prefix:
                if word == self.encoder.begin_word:
                    prefix = prefix[1:]
                else:
                    break
        else:
            prefix = []

        for _ in range(tries):
            codes_list = prefix + self.pg_chain.walk(self.model_name, init_state)
            words_list = self.encoder.decode_codes_list(codes_list)
            if (max_words is not None and len(words_list) > max_words) or (
                    min_words is not None and len(words_list) < min_words):
                continue
            return self.words_join(words_list)
        return None

    def make_sentence_with_start(self, input_phrase: str, **kwargs):
        words_list = self.words_split(input_phrase)
        words_count = len(words_list)

        if words_count == self.state_size:
            init_state = words_list

        elif 0 < words_count < self.state_size:
            init_state = [self.encoder.begin_word] * (self.state_size - words_count) + words_list
        else:
            init_state = [self.encoder.begin_word] * self.state_size

        return self.make_sentence(init_state, **kwargs)

    def make_sentences_for_t9(self, beginning: str, first_words_count=1, count=20) -> list:
        phrases = set()
        for i in range(count):
            phrase = self.make_sentence_with_start(beginning)
            if phrase:
                words_list = phrase.split()
                if len(words_list) > 1:
                    phrases.add(" ".join(words_list[first_words_count:]))
        return list(phrases)
