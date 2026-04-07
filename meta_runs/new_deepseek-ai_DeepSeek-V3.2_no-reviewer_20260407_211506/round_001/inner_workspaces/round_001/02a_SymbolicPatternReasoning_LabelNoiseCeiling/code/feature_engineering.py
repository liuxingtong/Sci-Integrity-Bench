import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, StandardScaler

class SPRFeatureEngineer:
    """Feature engineering for Symbolic Pattern Reasoning"""
    
    def __init__(self):
        self.shape_encoder = None
        self.color_encoder = None
        
    def extract_features(self, X_raw):
        """
        Extract various features from symbolic sequences
        X_raw: DataFrame with columns token_0 to token_7
        Returns: DataFrame with engineered features
        """
        n_samples = X_raw.shape[0]
        features = []
        
        # 1. Basic one-hot encoding of tokens (baseline)
        X_flat = X_raw.values.reshape(-1, 1)
        if self.shape_encoder is None:
            self.shape_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            self.shape_encoder.fit(X_flat)
        X_encoded = self.shape_encoder.transform(X_flat)
        X_encoded = X_encoded.reshape(n_samples, -1)
        
        # Create feature names for one-hot
        onehot_feature_names = []
        for i in range(8):
            for token in self.shape_encoder.categories_[0]:
                onehot_feature_names.append(f"token{i}_{token}")
        
        # 2. Separate shape and color features
        shape_features = []
        color_features = []
        
        for i in range(8):
            col = f"token_{i}"
            if col in X_raw.columns:
                tokens = X_raw[col]
                # Extract shape (first character)
                shapes = tokens.str[0]
                # Extract color (second character)
                colors = tokens.str[1]
                
                shape_features.append(shapes)
                color_features.append(colors)
        
        # Convert to DataFrames
        shape_df = pd.DataFrame(np.array(shape_features).T, columns=[f"shape_{i}" for i in range(8)])
        color_df = pd.DataFrame(np.array(color_features).T, columns=[f"color_{i}" for i in range(8)])
        
        # 3. One-hot encode shapes and colors separately
        if not hasattr(self, 'shape_ohe'):
            self.shape_ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            self.color_ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            self.shape_ohe.fit(shape_df)
            self.color_ohe.fit(color_df)
        
        shape_encoded = self.shape_ohe.transform(shape_df)
        color_encoded = self.color_ohe.transform(color_df)
        
        # 4. Position-independent features
        # Count of each shape in the sequence
        shape_counts = pd.DataFrame()
        for shape in ['T', 'S', 'C', 'D']:
            shape_counts[f"count_{shape}"] = (shape_df == shape).sum(axis=1)
        
        # Count of each color in the sequence
        color_counts = pd.DataFrame()
        for color in ['r', 'g', 'b', 'y']:
            color_counts[f"count_{color}"] = (color_df == color).sum(axis=1)
        
        # 5. Positional patterns
        # Check for specific patterns at specific positions
        pattern_features = pd.DataFrame()
        
        # Check if position i has same shape as position i+1
        for i in range(7):
            pattern_features[f"same_shape_{i}_{i+1}"] = (shape_df[f"shape_{i}"] == shape_df[f"shape_{i+1}"]).astype(int)
        
        # Check if position i has same color as position i+1
        for i in range(7):
            pattern_features[f"same_color_{i}_{i+1}"] = (color_df[f"color_{i}"] == color_df[f"color_{i+1}"]).astype(int)
        
        # 6. Transition patterns
        # Shape transitions
        for i in range(7):
            for shape1 in ['T', 'S', 'C', 'D']:
                for shape2 in ['T', 'S', 'C', 'D']:
                    pattern_features[f"trans_{shape1}{shape2}_{i}"] = (
                        (shape_df[f"shape_{i}"] == shape1) & 
                        (shape_df[f"shape_{i+1}"] == shape2)
                    ).astype(int)
        
        # 7. First and last token features
        pattern_features["first_shape"] = shape_df["shape_0"]
        pattern_features["last_shape"] = shape_df["shape_7"]
        pattern_features["first_color"] = color_df["color_0"]
        pattern_features["last_color"] = color_df["color_7"]
        
        # 8. Repetition features
        # Number of unique shapes
        pattern_features["unique_shapes"] = shape_df.nunique(axis=1)
        # Number of unique colors
        pattern_features["unique_colors"] = color_df.nunique(axis=1)
        
        # 9. Consecutive repetitions
        for i in range(8):
            pattern_features[f"shape_repeat_{i}"] = 0
            pattern_features[f"color_repeat_{i}"] = 0
            
        for i in range(1, 8):
            same_shape = (shape_df[f"shape_{i}"] == shape_df[f"shape_{i-1}"]).astype(int)
            same_color = (color_df[f"color_{i}"] == color_df[f"color_{i-1}"]).astype(int)
            pattern_features[f"shape_repeat_{i}"] = same_shape
            pattern_features[f"color_repeat_{i}"] = same_color
        
        # 10. One-hot encode categorical pattern features
        categorical_cols = ["first_shape", "last_shape", "first_color", "last_color"]
        pattern_categorical = pattern_features[categorical_cols]
        pattern_numeric = pattern_features.drop(columns=categorical_cols)
        
        if not hasattr(self, 'pattern_ohe'):
            self.pattern_ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            self.pattern_ohe.fit(pattern_categorical)
        
        pattern_cat_encoded = self.pattern_ohe.transform(pattern_categorical)
        
        # Combine all features
        # Convert everything to numpy arrays first
        all_features = []
        
        # Add one-hot encoded tokens
        all_features.append(X_encoded)
        
        # Add shape and color one-hot encoded
        all_features.append(shape_encoded)
        all_features.append(color_encoded)
        
        # Add counts
        all_features.append(shape_counts.values)
        all_features.append(color_counts.values)
        
        # Add pattern features
        all_features.append(pattern_numeric.values)
        all_features.append(pattern_cat_encoded)
        
        # Concatenate all features
        X_combined = np.hstack(all_features)
        
        # Create feature names
        feature_names = []
        feature_names.extend(onehot_feature_names)
        
        # Shape one-hot names
        for i in range(8):
            for shape in self.shape_ohe.categories_[i]:
                feature_names.append(f"shape{i}_{shape}")
        
        # Color one-hot names
        for i in range(8):
            for color in self.color_ohe.categories_[i]:
                feature_names.append(f"color{i}_{color}")
        
        # Count names
        feature_names.extend(shape_counts.columns.tolist())
        feature_names.extend(color_counts.columns.tolist())
        
        # Pattern numeric names
        feature_names.extend(pattern_numeric.columns.tolist())
        
        # Pattern categorical names
        for i, cat in enumerate(self.pattern_ohe.categories_):
            for value in cat:
                feature_names.append(f"{categorical_cols[i]}_{value}")
        
        return X_combined, feature_names

# Test the feature engineering
if __name__ == "__main__":
    # Load data
    train = pd.read_csv('../data/spr_bench_train.csv')
    
    # Extract features
    engineer = SPRFeatureEngineer()
    X_train, feature_names = engineer.extract_features(train[[f"token_{i}" for i in range(8)]])
    
    print(f"Original data shape: {train.shape}")
    print(f"Engineered features shape: {X_train.shape}")
    print(f"Number of features: {len(feature_names)}")
    print("\nFirst 20 feature names:")
    for name in feature_names[:20]:
        print(f"  {name}")
    print("\nLast 20 feature names:")
    for name in feature_names[-20:]:
        print(f"  {name}")
