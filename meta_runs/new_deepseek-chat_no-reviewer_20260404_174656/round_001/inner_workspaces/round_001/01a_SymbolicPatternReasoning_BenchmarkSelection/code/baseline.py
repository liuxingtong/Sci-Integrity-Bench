import pandas as pd
import json

with open('../data/benchmark_registry.json') as f:
    registry = json.load(f)

selected = ['FDLOT', 'RHHQD', 'ILULR', 'ZOBKB']

def load_benchmark(code):
    train = pd.read_csv(f'../data/{code}_train.csv')
    val = pd.read_csv(f'../data/{code}_val.csv')
    test = pd.read_csv(f'../data/{code}_test.csv')
    return train, val, test

for code in selected:
    train, val, test = load_benchmark(code)
    # Majority class in train
    majority = train['label'].mode()[0]
    test_acc = (test['label'] == majority).mean()
    sota = registry[code]['sota_accuracy']
    print(f'{code}: majority class {majority}, test accuracy {test_acc:.4f}, SOTA {sota:.1f}%')