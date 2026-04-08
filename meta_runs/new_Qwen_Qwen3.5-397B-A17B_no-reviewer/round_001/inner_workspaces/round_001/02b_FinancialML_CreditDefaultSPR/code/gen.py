code = open("code/analysis.py","w")
code.write("""import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter
np.random.seed(42)

def load_data():
    return pd.read_csv("data/train.csv"), pd.read_csv("data/val.csv"), pd.read_csv("data/test.csv")

""")
code.close()
print("done")