import pandas as pd
import numpy as np
from scipy import stats, signal
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, StratifiedKFold
import os

# Set up paths
data_dir = '../data'
output_dir = '../outputs'

# Load data
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
test_df = pd.read_csv(os.path.join(data_dir, 'test.csv'))

# SAX symbols in likely order (brightness increasing)
# Assuming '.' is dimmest, '*' is brighter, then letters
# Based on typical SAX: symbols ordered by value ranges
sax_symbols = ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']
symbol_to_value = {sym: i for i, sym in enumerate(sax_symbols)}

print(f"SAX symbol order (dimmest to brightest): {sax_symbols}")
print(f"Symbol to value mapping: {symbol_to_value}")

# Convert to numeric time series
def sax_to_numeric(series):
    return [symbol_to_value[ch] for ch in series]

# Extract comprehensive time series features
def extract_ts_features(numeric_series):
    features = {}
    ts = np.array(numeric_series)
    n = len(ts)
    
    # 1. Basic statistical features
    features['mean'] = np.mean(ts)
    features['std'] = np.std(ts)
    features['skew'] = stats.skew(ts) if n > 2 else 0
    features['kurtosis'] = stats.kurtosis(ts) if n > 3 else 0
    features['median'] = np.median(ts)
    features['min'] = np.min(ts)
    features['max'] = np.max(ts)
    features['range'] = features['max'] - features['min']
    
    # 2. Percentile-based features
    for p in [10, 25, 50, 75, 90]:
        features[f'p{p}'] = np.percentile(ts, p)
    features['iqr'] = features['p75'] - features['p25']
    
    # 3. Linear trend
    x = np.arange(n)
    slope, intercept = np.polyfit(x, ts, 1)
    features['trend_slope'] = slope
    features['trend_intercept'] = intercept
    
    # Residuals from trend
    residuals = ts - (slope * x + intercept)
    features['trend_residual_std'] = np.std(residuals)
    
    # 4. Autocorrelation features
    for lag in [1, 2, 3, 5, 10]:
        if lag < n:
            corr = np.corrcoef(ts[:-lag], ts[lag:])[0, 1]
            features[f'acf{lag}'] = corr if not np.isnan(corr) else 0
    
    # 5. Simple nonlinear features
    # Mean crossing rate
    mean_val = np.mean(ts)
    crossings = np.sum(np.diff(ts > mean_val) != 0)
    features['mean_crossings'] = crossings
    features['mean_crossing_rate'] = crossings / (n - 1) if n > 1 else 0
    
    # 6. Peak/valley features
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(ts, height=np.mean(ts))
    valleys, _ = find_peaks(-ts, height=-np.mean(ts))
    features['n_peaks'] = len(peaks)
    features['n_valleys'] = len(valleys)
    features['peak_valley_ratio'] = len(peaks) / max(1, len(valleys))
    
    if len(peaks) > 0:
        features['mean_peak_height'] = np.mean(ts[peaks])
        features['max_peak_height'] = np.max(ts[peaks])
    else:
        features['mean_peak_height'] = 0
        features['max_peak_height'] = 0
    
    # 7. Sequential features
    # Number of times series increases/decreases
    diffs = np.diff(ts)
    features['n_increases'] = np.sum(diffs > 0)
    features['n_decreases'] = np.sum(diffs < 0)
    features['n_constant'] = np.sum(diffs == 0)
    
    # 8. Run length features
    from itertools import groupby
    runs = [sum(1 for _ in group) for _, group in groupby(ts)]
    features['max_run_length'] = max(runs) if runs else 0
    features['mean_run_length'] = np.mean(runs) if runs else 0
    features['run_std'] = np.std(runs) if runs and len(runs) > 1 else 0
    
    # 9. Fourier features
    try:
        fft = np.fft.fft(ts - np.mean(ts))
        freqs = np.fft.fftfreq(n)
        magnitudes = np.abs(fft)
        
        # Get positive frequencies only
        pos_mask = freqs > 0
        if np.any(pos_mask):
            pos_freqs = freqs[pos_mask]
            pos_mags = magnitudes[pos_mask]
            
            # Dominant frequency
            max_idx = np.argmax(pos_mags)
            features['dominant_freq'] = pos_freqs[max_idx]
            features['dominant_mag'] = pos_mags[max_idx]
            
            # Spectral centroid
            features['spectral_centroid'] = np.sum(pos_freqs * pos_mags) / np.sum(pos_mags)
        else:
            features['dominant_freq'] = 0
            features['dominant_mag'] = 0
            features['spectral_centroid'] = 0
    except:
        features['dominant_freq'] = 0
        features['dominant_mag'] = 0
        features['spectral_centroid'] = 0
    
    return features

# Extract features for all datasets
print("Extracting SAX-based time series features...")

def extract_features_for_df(df):
    features_list = []
    for idx, row in df.iterrows():
        numeric_series = sax_to_numeric(row['symbol_series'])
        features = extract_ts_features(numeric_series)
        features['field_id'] = int(row['field_id'][3:])
        features['label'] = row['label']
        features_list.append(features)
    return pd.DataFrame(features_list)

train_features = extract_features_for_df(train_df)
val_features = extract_features_for_df(val_df)
test_features = extract_features_for_df(test_df)

print(f"Training features shape: {train_features.shape}")
print(f"Validation features shape: {val_features.shape}")
print(f"Test features shape: {test_features.shape}")

# Prepare data
feature_cols = [col for col in train_features.columns if col not in ['label']]
X_train = train_features[feature_cols].values
y_train = train_features['label'].values
X_val = val_features[feature_cols].values
y_val = val_features['label'].values
X_test = test_features[feature_cols].values
y_test = test_features['label'].values

print(f"\nNumber of features: {len(feature_cols)}")
print(f"Feature names: {feature_cols}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Try multiple models
models = {
    'RF': RandomForestClassifier(n_estimators=200, max_depth=10, 
                                 random_state=42, class_weight='balanced'),
    'GB': GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, 
                                     max_depth=5, random_state=42),
    'SVM': SVC(kernel='rbf', C=1.0, gamma='scale', 
               random_state=42, class_weight='balanced', probability=True),
}

results = {}
for name, model in models.items():
    print(f"\n=== Training {name} ===")
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='balanced_accuracy')
    
    # Train
    model.fit(X_train_scaled, y_train)
    
    # Validation
    y_val_pred = model.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, y_val_pred)
    
    print(f"CV mean accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    print(f"Validation accuracy: {val_acc:.4f}")
    
    results[name] = {
        'model': model,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'val_acc': val_acc
    }

# Best model
best_name = max(results, key=lambda x: results[x]['val_acc'])
best_model = results[best_name]['model']
print(f"\n=== Best Model: {best_name} ===")
print(f"Validation accuracy: {results[best_name]['val_acc']:.4f}")

# Test evaluation
y_test_pred = best_model.predict(X_test_scaled)
test_acc = balanced_accuracy_score(y_test, y_test_pred)
print(f"\nTest accuracy: {test_acc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_test_pred))

# Feature importance
if hasattr(best_model, 'feature_importances_'):
    print("\n=== Top 20 Feature Importances ===")
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    for i in range(min(20, len(feature_cols))):
        print(f"{i+1:2d}. {feature_cols[indices[i]]}: {importances[indices[i]]:.4f}")

print("\nSAX-based approach complete!")
