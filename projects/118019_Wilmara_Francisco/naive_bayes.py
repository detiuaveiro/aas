import pandas as pd
from functools import reduce

likelihood_spam: {}
likelihood_ham: {}
train_spam = []
train_ham = []
prior_spam: {}
prior_ham: {}


def bayes(txt):
    probs_spam = []
    probs_ham = []

    txt_as_list = txt.split()
    for w in txt_as_list:
        if w in likelihood_spam:
            pr_WS = likelihood_spam[w]
        else:
            pr_WS = 1.0 / (len(train_spam) + 2)

        if w in likelihood_ham:
            pr_WH = likelihood_ham[w]
        else:
            pr_WH = 1.0 / (len(train_ham) + 2)

        probs_spam.append(pr_WS)
        probs_ham.append(pr_WH)

    p_if_spam = prior_spam * reduce(lambda num1, num2: num1 * num2, probs_spam, 1.0)
    p_if_ham = prior_ham * reduce(lambda num1, num2: num1 * num2, probs_ham, 1.0)
    return p_if_spam / (p_if_spam + p_if_ham)


def compute_likelihood(vocab, train):
    likelihood = {}
    for w in vocab:
        count = 0
        for sentence in train:
            if w in sentence:
                #print(w+":", sentence)
                count += 1
        #print(f"Number of ham emails with the word '{w}': {count}")
        prob = (count + 1)/(len(train) + 2)
        #print(f"Hamicity of the word '{w}': {prob} ")
        likelihood[w.lower()] = prob
    return likelihood


def naive_bayes_algo():
    # make a vocabulary of unique words that occur in known spam emails
    vocab_words_spam = []

    for sentence in train_spam:
        sentence_as_list = sentence.split()
        for word in sentence_as_list:
            vocab_words_spam.append(word)
    vocab_words_spam = list(set(vocab_words_spam))

    #print(vocab_words_spam)

    vocab_words_ham = []

    for sentence in train_ham:
        sentence_as_list = sentence.split()
        for word in sentence_as_list:
            vocab_words_ham.append(word)
    vocab_words_ham = list(set(vocab_words_ham))

    #print(vocab_words_ham)

    global likelihood_spam, likelihood_ham

    likelihood_spam = compute_likelihood(vocab_words_spam, train_spam)

    likelihood_ham = compute_likelihood(vocab_words_ham, train_ham)

    global prior_spam, prior_ham
    prior_spam = len(train_spam) / (len(train_spam) + (len(train_ham)))
    #print(f'Prior prob HAM: {prior_spam}')
    prior_ham = len(train_ham) / (len(train_spam) + (len(train_ham)))
    #print(f'Prior prob HAM: {prior_ham}')


def test_algo(test_emails):
    for label, emails in test_emails.items():
        for sentence in emails:
            prob_spam = bayes(sentence)
            print(f'{label} - {sentence} -> Probability: {prob_spam:.4f}')


def train_algorithm():
    file_path = 'spam.csv'
    data = pd.read_csv(file_path)
    global train_spam, train_ham

    # Split data into spam and ham based on 'Category'
    spam_data = data[data['Category'] == 'spam']
    ham_data = data[data['Category'] == 'ham']

    train_spam = spam_data['Message'].tolist()
    train_ham = ham_data['Message'].tolist()

    naive_bayes_algo()
