import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

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
                
        # Convert to probabilities with Laplace smoothing
        self.probs = defaultdict(lambda: defaultdict(float))
        vocab_size = 6 # A, B, C, D, 1, 2
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

train_0 = train[train['default_flag'] == 0]['sym_seq']
train_1 = train[train['default_flag'] == 1]['sym_seq']

for order in [1, 2, 3, 4, 5, 6, 7, 8]:
    for smoothing in [1e-6, 1e-3, 0.1, 1.0]:
        model_0 = MarkovModel(order=order, smoothing=smoothing)
        model_0.fit(train_0)
        
        model_1 = MarkovModel(order=order, smoothing=smoothing)
        model_1.fit(train_1)
        
        y_val_pred = []
        for seq in val['sym_seq']:
            score_0 = model_0.score(seq)
            score_1 = model_1.score(seq)
            y_val_pred.append(score_1 - score_0)
            
        auc = roc_auc_score(val['default_flag'], y_val_pred)
        print(f'Markov Order: {order}, Smoothing: {smoothing} -> Val AUC: {auc:.4f}')
