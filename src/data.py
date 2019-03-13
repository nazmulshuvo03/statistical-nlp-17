"""
Methods and tools to work with the pre-processed CSVs.
"""
import json

from collections import defaultdict, Counter

from torchtext.data import Field, TabularDataset
from torchtext.vocab import Vocab


def simple_tokenizer(text):
    """
    Simple tokenizer which splits the token by the space
    character. The CSVs have already been pre-processed with
    spaCy, therefore this should be enough.

    Parameters
    ---
    text : str
        Input text to tokenize.

    Returns
    ---
    iterator
        Iterator over token text.
    """
    return text.split(' ')


def store_vocab(vocab, file_path):
    """
    Stores a vocab in a JSON file.

    Inspired by https://github.com/pytorch/text/issues/253#issue-305929871

    Parameters
    ---
    vocab : torchtext.Vocab
        Vocabulary with our corpus.
    file_path : str
        Path to the vocab state to write.

    """
    vocab_state = dict(vocab.__dict__, stoi=dict(vocab.stoi))
    with open(file_path, 'w') as file:
        json.dump(vocab_state, file)


def read_vocab(file_path):
    """
    Rads a vocab from its previously stored state.

    Inspired by https://github.com/pytorch/text/issues/253#issue-305929871

    Parameters
    ---
    file_path : str
        Path to the JSON file with the vocab info.

    Returns
    ---
    vocab : torchtext.Vocab
        Vocabulary created.
    """
    vocab_state = {}
    with open(file_path) as file:
        vocab_state = json.load(file)

    vocab = Vocab(Counter())
    vocab.__dict__.update(vocab_state)
    vocab.stoi = defaultdict(lambda: 0, vocab.stoi)
    return vocab


def read_data_set(file_path, vocab):
    """
    Reads the data set from one of the pre-processed CSVs composed
    of columns `label` and `sentence`.

    Parameters
    ---
    file_path : str
        Path to the CSV file.
    vocab : torchtext.Vocab
        Vocabulary to use.

    Returns
    ---
    X : torch.Tensor[num_labels x num_examples x sen_length]
        Sentences on the dataset grouped by labels.
    y : torch.Tensor[num_labels]
        Labels for each group of sentences.
    """
    sentence = Field(
        batch_first=True, sequential=True, tokenize=simple_tokenizer)
    sentence.vocab = vocab

    label = Field(is_target=True)
    label.vocab = vocab

    data_set = TabularDataset(
        path=file_path,
        format='csv',
        skip_header=True,
        fields=[('label', label), ('sentence', sentence)])

    sentences_tensor = sentence.process(data_set.sentence)
    y = label.process(data_set.label).squeeze()

    # Infer num_labels and group sentences by label
    num_labels = y.unique().shape[0]
    sen_length = sentences_tensor.shape[-1]
    X = sentences_tensor.view(num_labels, -1, sen_length)

    return X, y


def generate_vocab(file_path):
    """
    Generate the vocabulary from one of the pre-processed CSVs composed
    of columns `label` and `sentence`.

    Parameters
    ---
    file_path : str
        Path to the CSV file.

    Returns
    ---
    vocab : torchtext.Vocab
        Vocabulary generated from the file.
    """
    text = Field(sequential=True, tokenize=simple_tokenizer)

    data_set = TabularDataset(
        path=file_path,
        format='csv',
        skip_header=True,
        fields=[('label', text), ('sentence', text)])

    text.build_vocab(data_set.label, data_set.sentence)
    return text.vocab