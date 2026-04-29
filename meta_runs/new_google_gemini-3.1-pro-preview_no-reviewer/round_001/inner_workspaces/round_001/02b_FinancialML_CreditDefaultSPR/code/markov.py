import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.metrics import roc_auc_score

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')

class MarkovModel:
    def __init__(self, order=1):
        self.order = order
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.totals = defaultdict(int)
        
    def fit(self, sequences):
        for seq in sequences:
            for i in range(len(seq) - self.order):
                state = seq[i:i+self.order]
                next_char = seq[i+self.order]
                self.transitions[state][next_char] += 1
                self.totals[state] += 1
                
        # Convert to probabilities
        self.probs = defaultdict(lambda: defaultdict(float))
        for state, next_chars in self.transitions.items():
            for next_char, count in next_chars.items():
                self.probs[state][next_char] = count / self.totals[state]
                
    def score(self, seq):
        log_prob = 0
        for i in range(len(seq) - self.order):
            state = seq[i:i+self.order]
            next_char = seq[i+self.order]
            prob = self.probs[state].get(next_char, 1e-6) # Smoothing
            log_prob += np.log(prob)
        return log_prob

train_0 = train[train['default_flag'] == 0]['sym_seq']
train_1 = train[train['default_flag'] == 1]['sym_seq']

for order in [1, 2, 3, 4, 5]:
    print(f'\n--- Markov Order: {order} ---')
    model_0 = MarkovModel(order=order)
    model_0.fit(train_0)
    
    model_1 = MarkovModel(order=order)
    model_1.fit(train_1)
    
    y_val_pred = []
    for seq in val['sym_seq']:
        score_0 = model_0.score(seq)
        score_1 = model_1.score(seq)
        y_val_pred.append(score_1 - score_0)
        
    auc = roc_auc_score(val['default_flag'], y_val_pred)
    print(f'Markov Val AUC: {auc:.4f}')
