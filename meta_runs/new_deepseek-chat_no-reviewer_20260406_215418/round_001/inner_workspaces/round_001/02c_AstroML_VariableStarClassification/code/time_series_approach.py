import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats, signal
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, StratifiedKFold
import os

# Set up paths
data_dir = '../data'
output_dir = '../outputs'
report_img_dir = '../report/images'

# Load data
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
test_df = pd.read_csv(os.path.join(data_dir, 'test.csv'))

# Define symbol ordering by likely brightness
# Assuming: * = brightest, then v, w, x, y, z, u, . = dimmest
# Or maybe alphabetical order corresponds to something?
# Let's try different orderings
symbol_orderings = {
    'ordering1': {'*': 7, 'v': 6, 'w': 5, 'x': 4, 'y': 3, 'z': 2, 'u': 1, '.': 0},  # * brightest
    'ordering2': {'.': 0, 'u': 1, 'z': 2, 'y': 3, 'x': 4, 'w': 5, 'v': 6, '*': 7},  # * dimmest
    'ordering3': {'*': 0, '.': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, 'u': 7},  # Different
}

# Convert symbol series to numeric time series
def series_to_numeric(series, ordering):
    return [ordering[ch] for ch in series]

# Extract time series features
def extract_ts_features(numeric_series):
    features = {}
    ts = np.array(numeric_series)
    
    # Basic statistics
    features['mean'] = np.mean(ts)
    features['std'] = np.std(ts)
    features['skew'] = stats.skew(ts)
    features['kurtosis'] = stats.kurtosis(ts)
    
    # Range and percentiles
    features['min'] = np.min(ts)
    features['max'] = np.max(ts)
    features['range'] = features['max'] - features['min']
    features['q25'] = np.percentile(ts, 25)
    features['q75'] = np.percentile(ts, 75)
    features['iqr'] = features['q75'] - features['q25']
    
    # Time series features
    # Autocorrelation at lag 1
    if len(ts) > 1:
        autocorr = np.corrcoef(ts[:-1], ts[1:])[0, 1]
        features['autocorr1'] = autocorr if not np.isnan(autocorr) else 0
    
    # Simple trend: linear regression slope
    x = np.arange(len(ts))
    slope, intercept = np.polyfit(x, ts, 1)
    features['trend_slope'] = slope
    
    # Number of peaks and valleys
    # Find local maxima and minima
    from scipy.signal import argrelextrema
    if len(ts) > 2:
        maxima = argrelextrema(ts, np.greater)[0]
        minima = argrelextrema(ts, np.less)[0]
        features['n_peaks'] = len(maxima)
        features['n_valleys'] = len(minima)
    else:
        features['n_peaks'] = 0
        features['n_valleys'] = 0
    
    # Periodicity: try to find dominant frequency
    try:
        fft = np.fft.fft(ts - np.mean(ts))
        freqs = np.fft.fftfreq(len(ts))
        # Get magnitude of positive frequencies
        pos_freqs = freqs[freqs > 0]
        magnitudes = np.abs(fft[freqs > 0])
        if len(magnitudes) > 0:
            features['dominant_freq'] = pos_freqs[np.argmax(magnitudes)]
            features['max_fft_mag'] = np.max(magnitudes)
        else:
            features['dominant_freq'] = 0
            features['max_fft_mag'] = 0
    except:
        features['dominant_freq'] = 0
        features['max_fft_mag'] = 0
    
    # Simple features: number of times series crosses its mean
    mean_crossings = np.sum(np.diff(ts > np.mean(ts)) != 0)
    features['mean_crossings'] = mean_crossings
    
    return features

# Try different orderings
for ordering_name, ordering in symbol_orderings.items():
    print(f"\n=== Trying {ordering_name} ===")
    
    # Extract features
    train_features_list = []
    for idx, row in train_df.iterrows():
        numeric_series = series_to_numeric(row['symbol_series'], ordering)
        features = extract_ts_features(numeric_series)
        features['label'] = row['label']
        features['field_id'] = int(row['field_id'][3:])
        train_features_list.append(features)
    
    val_features_list = []
    for idx, row in val_df.iterrows():
        numeric_series = series_to_numeric(row['symbol_series'], ordering)
        features = extract_ts_features(numeric_series)
        features['label'] = row['label']
        features['field_id'] = int(row['field_id'][3:])
        val_features_list.append(features)
    
    test_features_list = []
    for idx, row in test_df.iterrows():
        numeric_series = series_to_numeric(row['symbol_series'], ordering)
        features = extract_ts_features(numeric_series)
        features['label'] = row['label']
        features['field_id'] = int(row['field_id'][3:])
        test_features_list.append(features)
    
    train_features = pd.DataFrame(train_features_list)
    val_features = pd.DataFrame(val_features_list)
    test_features = pd.DataFrame(test_features_list)
    
    print(f"Features shape: {train_features.shape}")
    
    # Prepare data
    feature_cols = [col for col in train_features.columns if col not in ['label']]
    X_train = train_features[feature_cols].values
    y_train = train_features['label'].values
    X_val = val_features[feature_cols].values
    y_val = val_features['label'].values
    X_test = test_features[feature_cols].values
    y_test = test_features['label'].values
    
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='balanced_accuracy')
    
    # Train and evaluate
    model.fit(X_train_scaled, y_train)
    y_val_pred = model.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, y_val_pred)
    
    print(f"CV mean accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    print(f"Validation accuracy: {val_acc:.4f}")
    
    # Test
    y_test_pred = model.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, y_test_pred)
    print(f"Test accuracy: {test_acc:.4f}")
    
    # Simple baseline: always predict the majority class
    from sklearn.dummy import DummyClassifier
    dummy = DummyClassifier(strategy='stratified', random_state=42)
    dummy.fit(X_train, y_train)
    dummy_acc = balanced_accuracy_score(y_test, dummy.predict(X_test))
    print(f"Random baseline: {dummy_acc:.4f}")

# Let's also try a very simple approach: just use symbol frequencies
print("\n=== Simple Frequency Approach ===")
# Just use symbol frequencies as features
def extract_simple_freq_features(df):
    symbols = ['*', 'v', 'w', 'z', 'y', 'u', '.', 'x']
    features_list = []
    
    for idx, row in df.iterrows():
        series = row['symbol_series']
        features = {}
        total = len(series)
        
        for sym in symbols:
            features[f'freq_{sym}'] = series.count(sym) / total
        
        features['label'] = row['label']
        features['field_id'] = int(row['field_id'][3:])
        features_list.append(features)
    
    return pd.DataFrame(features_list)

train_simple = extract_simple_freq_features(train_df)
val_simple = extract_simple_freq_features(val_df)
test_simple = extract_simple_freq_features(test_df)

feature_cols = [col for col in train_simple.columns if col not in ['label']]
X_train = train_simple[feature_cols].values
y_train = train_simple['label'].values
X_val = val_simple[feature_cols].values
y_val = val_simple['label'].values
X_test = test_simple[feature_cols].values
y_test = test_simple['label'].values

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
model.fit(X_train_scaled, y_train)

y_val_pred = model.predict(X_val_scaled)
val_acc = balanced_accuracy_score(y_val, y_val_pred)
y_test_pred = model.predict(X_test_scaled)
test_acc = balanced_accuracy_score(y_test, y_test_pred)

print(f"Simple frequency features - Validation: {val_acc:.4f}, Test: {test_acc:.4f}")
