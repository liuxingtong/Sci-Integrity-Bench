import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

class MarkovModel:
    def __init__(self, order=1, smoothing=1e-6):
        self.order = order
        self.smoothing = smoothing
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.totals = defaultdict(int)
        
    def fit(self, sequences):
        for seq in sequences:
            for i in range(len(seq) - self.order):
                state = seq[i:i+self.order]
                next_char = seq[i+self.order]
                self.transitions[state][next_char] += 1
                self.totals[state] += 1
                
        self.probs = defaultdict(lambda: defaultdict(float))
        vocab_size = 6
        for state in self.transitions.keys():
            for next_char in ['A', 'B', 'C', 'D', '1', '2']:
                count = self.transitions[state].get(next_char, 0)
                self.probs[state][next_char] = (count + self.smoothing) / (self.totals[state] + self.smoothing * vocab_size)
                
    def score(self, seq):
        log_prob = 0
        vocab_size = 6
        for i in range(len(seq) - self.order):
            state = seq[i:i+self.order]
            next_char = seq[i+self.order]
            if state in self.probs:
                prob = self.probs[state].get(next_char, self.smoothing / (self.totals[state] + self.smoothing * vocab_size))
            else:
                prob = 1.0 / vocab_size
            log_prob += np.log(prob)
        return log_prob

train_full = pd.concat([train, val])
train_0 = train_full[train_full['default_flag'] == 0]['sym_seq']
train_1 = train_full[train_full['default_flag'] == 1]['sym_seq']

order = 5
smoothing = 1.0

model_0 = MarkovModel(order=order, smoothing=smoothing)
model_0.fit(train_0)

model_1 = MarkovModel(order=order, smoothing=smoothing)
model_1.fit(train_1)

y_test_pred = []
for seq in test['sym_seq']:
    score_0 = model_0.score(seq)
    score_1 = model_1.score(seq)
    y_test_pred.append(score_1 - score_0)
    
test_auc = roc_auc_score(test['default_flag'], y_test_pred)
print(f'Markov Test AUC (Train+Val): {test_auc:.4f}')
