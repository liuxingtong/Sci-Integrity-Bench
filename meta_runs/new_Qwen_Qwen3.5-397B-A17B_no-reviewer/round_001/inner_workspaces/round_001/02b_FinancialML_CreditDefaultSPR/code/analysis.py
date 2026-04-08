import pandas as pd
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

def extract_sequence_features(seq):
    features = {}
    features["length"] = len(seq)
    char_counts = Counter(seq)
    for char in ["A", "B", "C", "D", "1", "2"]:
        features["count_"+char] = char_counts.get(char, 0)
    features["ratio_numeric"] = (char_counts.get("1", 0) + char_counts.get("2", 0)) / len(seq)
    features["ratio_A"] = char_counts.get("A", 0) / len(seq)
    features["ratio_B"] = char_counts.get("B", 0) / len(seq)
    features["ratio_C"] = char_counts.get("C", 0) / len(seq)
    features["ratio_D"] = char_counts.get("D", 0) / len(seq)
    features["ratio_1"] = char_counts.get("1", 0) / len(seq)
    features["ratio_2"] = char_counts.get("2", 0) / len(seq)
    char_to_num = {"A": 0, "B": 1, "C": 2, "D": 3, "1": 4, "2": 5}
    features["first_char"] = char_to_num.get(seq[0], -1)
    features["last_char"] = char_to_num.get(seq[-1], -1)
    mid = len(seq) // 2
    first_half = seq[:mid]
    second_half = seq[mid:]
    first_half_counts = Counter(first_half)
    second_half_counts = Counter(second_half)
    for char in ["A", "B", "C", "D", "1", "2"]:
        features["first_half_"+char] = first_half_counts.get(char, 0) / max(len(first_half), 1)
        features["second_half_"+char] = second_half_counts.get(char, 0) / max(len(second_half), 1)
    bigrams = [seq[i:i+2] for i in range(len(seq)-1)]
    bigram_counts = Counter(bigrams)
    important_bigrams = ["AA", "AB", "AC", "AD", "BA", "BB", "BC", "BD", "CA", "CB", "CC", "CD", "DA", "DB", "DC", "DD", "11", "12", "21", "22", "A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D"]
    for bg in important_bigrams:
        features["bigram_"+bg] = bigram_counts.get(bg, 0) / max(len(bigrams), 1)
    transitions = 0
    for i in range(len(seq)-1):
        c1, c2 = seq[i], seq[i+1]
        if (c1 in "12") != (c2 in "12"):
            transitions += 1
    features["transition_count"] = transitions / max(len(seq)-1, 1)
    runs = 1
    for i in range(len(seq)-1):
        if seq[i] != seq[i+1]:
            runs += 1
    features["run_count"] = runs / max(len(seq), 1)
    features["avg_run_length"] = len(seq) / max(runs, 1)
    probs = np.array([char_counts.get(c, 0) / len(seq) for c in "ABCD12"])
    probs = probs[probs > 0]
    features["entropy"] = -np.sum(probs * np.log2(probs + 1e-10))
    return features

def create_features(df):
    feature_list = []
    for idx, row in df.iterrows():
        features = extract_sequence_features(row["sym_seq"])
        features["id"] = row["id"]
        features["default_flag"] = row["default_flag"]
        feature_list.append(features)
    return pd.DataFrame(feature_list)
print("Loading data...")
train, val, test = load_data()
print("Train:", len(train), "Val:", len(val), "Test:", len(test))
print("Extracting features...")
train_feat = create_features(train)
val_feat = create_features(val)
test_feat = create_features(test)
feature_cols = [c for c in train_feat.columns if c not in ["id", "default_flag"]]
X_train = train_feat[feature_cols].values
y_train = train_feat["default_flag"].values
X_val = val_feat[feature_cols].values
y_val = val_feat["default_flag"].values
X_test = test_feat[feature_cols].values
y_test = test_feat["default_flag"].values
print("Features:", len(feature_cols))
models = {"RandomForest": RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1), "GradientBoosting": GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42), "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42)}
results = {}
for name, model in models.items():
    print("Training", name)
    model.fit(X_train, y_train)
    train_pred = model.predict_proba(X_train)[:, 1]
    val_pred = model.predict_proba(X_val)[:, 1]
    test_pred = model.predict_proba(X_test)[:, 1]
    train_auc = roc_auc_score(y_train, train_pred)
    val_auc = roc_auc_score(y_val, val_pred)
    test_auc = roc_auc_score(y_test, test_pred)
    results[name] = {"model": model, "train_auc": train_auc, "val_auc": val_auc, "test_auc": test_auc, "test_pred": test_pred}
    print("  Train AUC:", round(train_auc,4), "Val AUC:", round(val_auc,4), "Test AUC:", round(test_auc,4))
best_model_name = max(results.keys(), key=lambda k: results[k]["val_auc"])
best_model = results[best_model_name]["model"]
print("Best model:", best_model_name)
if hasattr(best_model, "feature_importances_"):
    importance_df = pd.DataFrame({"feature": feature_cols, "importance": best_model.feature_importances_}).sort_values("importance", ascending=False)
    importance_df.to_csv("outputs/feature_importance.csv", index=False)
    plt.figure(figsize=(10, 8))
    top_features = importance_df.head(15)
    plt.barh(range(len(top_features)), top_features["importance"].values)
    plt.yticks(range(len(top_features)), top_features["feature"].values)
    plt.xlabel("Importance")
    plt.title("Top 15 Feature Importances")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig("report/images/feature_importance.png", dpi=150)
    plt.close()
plt.figure(figsize=(8, 6))
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res["test_pred"])
    auc_val = res["test_auc"]
    plt.plot(fpr, tpr, label=name+" (AUC="+str(round(auc_val,4))+")")
plt.plot([0, 1], [0, 1], "k--", label="Random")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curves on Test Set")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("report/images/roc_curves.png", dpi=150)
plt.close()
train_lengths = train["sym_seq"].apply(len)
plt.figure(figsize=(8, 6))
plt.hist(train_lengths, bins=20, alpha=0.7, color="steelblue")
plt.xlabel("Sequence Length")
plt.ylabel("Frequency")
plt.title("Distribution of Sequence Lengths (Train)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("report/images/sequence_lengths.png", dpi=150)
plt.close()
plt.figure(figsize=(8, 6))
splits = ["Train", "Validation", "Test"]
default_rates = [train["default_flag"].mean(), val["default_flag"].mean(), test["default_flag"].mean()]
plt.bar(splits, default_rates, color=["steelblue", "coral", "seagreen"])
plt.ylabel("Default Rate")
plt.title("Class Balance Across Splits")
plt.ylim(0, 1)
for i, v in enumerate(default_rates):
    plt.text(i, v + 0.02, str(round(v,3)), ha="center")
plt.tight_layout()
plt.savefig("report/images/class_balance.png", dpi=150)
plt.close()
train_feat_merged = train_feat.merge(train[["id", "default_flag"]], on="id")
char_cols = ["count_A", "count_B", "count_C", "count_D", "count_1", "count_2"]
plt.figure(figsize=(10, 6))
char_means_default = train_feat_merged[train_feat_merged["default_flag"]==1][char_cols].mean()
char_means_nondefault = train_feat_merged[train_feat_merged["default_flag"]==0][char_cols].mean()
x = np.arange(len(char_cols))
width = 0.35
plt.bar(x - width/2, char_means_default.values, width, label="Default", color="coral")
plt.bar(x + width/2, char_means_nondefault.values, width, label="Non-Default", color="steelblue")
plt.xticks(x, char_cols)
plt.ylabel("Mean Count")
plt.title("Character Counts by Default Status (Train)")
plt.legend()
plt.tight_layout()
plt.savefig("report/images/char_distribution.png", dpi=150)
plt.close()
