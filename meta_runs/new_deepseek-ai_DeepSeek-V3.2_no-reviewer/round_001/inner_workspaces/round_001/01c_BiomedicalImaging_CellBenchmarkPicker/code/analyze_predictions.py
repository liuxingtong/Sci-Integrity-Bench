import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Analyze D0013 specifically
dataset_id = 'D0013'
train_df = pd.read_csv(f'data/patches/{dataset_id}/train.csv')
val_df = pd.read_csv(f'data/patches/{dataset_id}/val.csv')
test_df = pd.read_csv(f'data/patches/{dataset_id}/test.csv')

print(f"Dataset {dataset_id}:")
print(f"Train class distribution: {dict(train_df['label'].value_counts().sort_index())}")
print(f"Val class distribution: {dict(val_df['label'].value_counts().sort_index())}")
print(f"Test class distribution: {dict(test_df['label'].value_counts().sort_index())}")

# Look at feature statistics
print(f"\nFeature statistics (train):")
print(train_df.drop('label', axis=1).describe().loc[['mean', 'std', 'min', 'max']])

# Train model and check predictions
X_train = train_df.drop('label', axis=1).values
y_train = train_df['label'].values
X_test = test_df.drop('label', axis=1).values
y_test = test_df['label'].values

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LogisticRegression(C=0.1, max_iter=1000, random_state=42)
model.fit(X_train_scaled, y_train)

y_test_pred = model.predict(X_test_scaled)
print(f"\nTest predictions vs true:")
for i in range(len(y_test)):
    print(f"  Sample {i}: true={y_test[i]}, pred={y_test_pred[i]}")

# Check decision function
if hasattr(model, 'decision_function'):
    dec_values = model.decision_function(X_test_scaled)
    print(f"\nDecision function values (shape: {dec_values.shape}):")
    print(dec_values)

# Check if classes are separable in feature space
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
X_train_pca = pca.fit_transform(X_train_scaled)
X_test_pca = pca.transform(X_test_scaled)

print(f"\nPCA explained variance ratio: {pca.explained_variance_ratio_}")
print(f"Total variance explained: {sum(pca.explained_variance_ratio_):.3f}")