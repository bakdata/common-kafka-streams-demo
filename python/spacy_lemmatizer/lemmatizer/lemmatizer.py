import spacy

from spacy_lemmatizer.lemmatizer import constants
from spacy_lemmatizer.models import Text, LemmaText

nlp = spacy.load(constants.spacy_model)


def process_text(text: Text):
    doc = nlp(text.content)
    lemmas = []
    for token in doc:
        if not token.is_stop and token.is_alpha:
            lemmas.append(token.lemma_.lower())

    lemma_text = LemmaText(lemmas)
    return lemma_text
