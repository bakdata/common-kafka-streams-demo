import pytest

from spacy_lemmatizer.models import Text, LemmaText


@pytest.fixture
def test_text():
    return Text(content='One morning, when Gregor Samsa woke from troubled dreams')


@pytest.fixture()
def test_lemma_text():
    lemmas = ['morning', 'gregor', 'samsa', 'wake', 'troubled', 'dream']

    return LemmaText(lemmas)
