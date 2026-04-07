import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neural_network import MLPClassifier
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product

# Load registry
with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)

# Selected benchmarks
selected_benchmarks = ["ZOBKB", "NUFES", "FDLOT", "GAPFD"]

def load_benchmark(code):
    train = pd.read_csv(f"../data/{code}_train.csv")
    val = pd.read_csv(f"../data/{code}_val.csv")
    test = pd.read_csv(f"../data/{code}_test.csv")
    return train, val, test

def preprocess_data_onehot(train, val, test):
    """Preprocess data using one-hot encoding"""
    token_cols = [col for col in train.columns if col.startswith('token_')]
    
    # Combine for consistent encoding
    all_data = pd.concat([train[token_cols], val[token_cols], test[token_cols]])
    
    # One-hot encode each position
    encoded_dfs = []
    for df in [train, val, test]:
        encoded_parts = []
        for col in token_cols:
            # One-hot encode this column
            dummies = pd.get_dummies(df[col], prefix=col)
            encoded_parts.append(dummies)
        
        # Combine all one-hot columns
        encoded_df = pd.concat(encoded_parts, axis=1)
        encoded_df['label'] = df['label'].values
        encoded_dfs.append(encoded_df)
    
    train_encoded, val_encoded, test_encoded = encoded_dfs
    
    # Prepare features and labels
    X_train = train_encoded.drop('label', axis=1).values
    y_train = train_encoded['label'].values
    
    X_val = val_encoded.drop('label', axis=1).values
    y_val = val_encoded['label'].values
    
    X_test = test_encoded.drop('label', axis=1).values
    y_test = test_encoded['label'].values
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def preprocess_data_label(train, val, test):
    """Preprocess data using label encoding"""
    token_cols = [col for col in train.columns if col.startswith('token_')]
    
    # Combine all data for consistent encoding
    all_data = pd.concat([train[token_cols], val[token_cols], test[token_cols]])
    
    # Create label encoders for each token position
    encoders = {}
    encoded_train = train.copy()
    encoded_val = val.copy()
    encoded_test = test.copy()
    
    for col in token_cols:
        le = LabelEncoder()
        le.fit(all_data[col])
        
        encoded_train[col] = le.transform(train[col])
        encoded_val[col] = le.transform(val[col])
        encoded_test[col] = le.transform(test[col])
        
        encoders[col] = le
    
    # Prepare features and labels
    X_train = encoded_train[token_cols].values
    y_train = encoded_train['label'].values
    
    X_val = encoded_val[token_cols].values
    y_val = encoded_val['label'].values
    
    X_test = encoded_test[token_cols].values
    y_test = encoded_test['label'].values
    
    return X_train, y_train, X_val, y_val, X_test, y_test, encoders

def train_model(model_type, X_train, y_train, X_val, y_val, hyperparams):
    """Train a model with given hyperparameters"""
    if model_type == 'rf':
        model = RandomForestClassifier(
            n_estimators=hyperparams.get('n_estimators', 100),
            max_depth=hyperparams.get('max_depth', None),
            random_state=42,
            n_jobs=-1
        )
    elif model_type == 'gb':
        model = GradientBoostingClassifier(
            n_estimators=hyperparams.get('n_estimators', 100),
            max_depth=hyperparams.get('max_depth', 3),
            learning_rate=hyperparams.get('learning_rate', 0.1),
            random_state=42
        )
    elif model_type == 'lr':
        model = LogisticRegression(
            C=hyperparams.get('C', 1.0),
            max_iter=1000,
            random_state=42
        )
    elif model_type == 'mlp':
        model = MLPClassifier(
            hidden_layer_sizes=hyperparams.get('hidden_layer_sizes', (100,)),
            alpha=hyperparams.get('alpha', 0.0001),
            max_iter=1000,
            random_state=42
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X_train, y_train)
    y_val_pred = model.predict(X_val)
    val_acc = accuracy_score(y_val, y_val_pred)
    
    return model, val_acc

def evaluate_models(code, X_train, y_train, X_val, y_val, X_test, y_test):
    """Evaluate multiple models on the benchmark"""
    
    # Define model configurations
    model_configs = {
        'rf': {
            'n_estimators': [50, 100, 200],
            'max_depth': [5, 10, 20, None]
        },
        'gb': {
            'n_estimators': [50, 100],
            'max_depth': [3, 5],
            'learning_rate': [0.01, 0.1]
        },
        'lr': {
            'C': [0.01, 0.1, 1.0, 10.0]
        },
        'mlp': {
            'hidden_layer_sizes': [(50,), (100,), (50, 50)],
            'alpha': [0.0001, 0.001, 0.01]
        }
    }
    
    best_models = {}
    
    for model_type, param_grid in model_configs.items():
        print(f"  Testing {model_type}...")
        
        # Generate all parameter combinations
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        param_combinations = [dict(zip(keys, v)) for v in product(*values)]
        
        best_val_acc = 0
        best_model = None
        best_params = {}
        
        for params in param_combinations:
            try:
                model, val_acc = train_model(model_type, X_train, y_train, X_val, y_val, params)
                
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    best_model = model
                    best_params = params
            except Exception as e:
                # Skip failed configurations
                continue
        
        if best_model is not None:
            # Evaluate on test set
            y_test_pred = best_model.predict(X_test)
            test_acc = accuracy_score(y_test, y_test_pred)
            
            best_models[model_type] = {
                'model': best_model,
                'params': best_params,
                'val_accuracy': best_val_acc * 100,
                'test_accuracy': test_acc * 100
            }
            
            print(f"    Best {model_type}: val={best_val_acc*100:.2f}%, test={test_acc*100:.2f}%")
    
    return best_models

def main():
    all_results = []
    
    for code in selected_benchmarks:
        print(f"\n=== Processing {code} ===")
        
        # Load data
        train, val, test = load_benchmark(code)
        print(f"Train: {train.shape}, Val: {val.shape}, Test: {test.shape}")
        
        # Try both preprocessing methods
        print("  Using label encoding:")
        X_train_le, y_train_le, X_val_le, y_val_le, X_test_le, y_test_le, _ = preprocess_data_label(train, val, test)
        
        # Evaluate models with label encoding
        models_le = evaluate_models(code, X_train_le, y_train_le, X_val_le, y_val_le, X_test_le, y_test_le)
        
        print("  Using one-hot encoding:")
        X_train_oh, y_train_oh, X_val_oh, y_val_oh, X_test_oh, y_test_oh = preprocess_data_onehot(train, val, test)
        
        # Scale data for LR and MLP (one-hot doesn't need scaling for tree-based models)
        scaler = StandardScaler()
        X_train_oh_scaled = scaler.fit_transform(X_train_oh)
        X_val_oh_scaled = scaler.transform(X_val_oh)
        X_test_oh_scaled = scaler.transform(X_test_oh)
        
        # Evaluate models with one-hot encoding
        models_oh = evaluate_models(code, X_train_oh_scaled, y_train_oh, X_val_oh_scaled, y_val_oh, X_test_oh_scaled, y_test_oh)
        
        # Get SOTA accuracy
        sota_acc = registry[code]['sota_accuracy']
        
        # Combine results
        for encoding, models in [('label', models_le), ('onehot', models_oh)]:
            for model_type, model_info in models.items():
                result = {
                    'code': code,
                    'encoding': encoding,
                    'model_type': model_type,
                    'params': str(model_info['params']),
                    'val_accuracy': model_info['val_accuracy'],
                    'test_accuracy': model_info['test_accuracy'],
                    'sota_accuracy': sota_acc,
                    'difference': model_info['test_accuracy'] - sota_acc
                }
                all_results.append(result)
        
        # Find best model for this benchmark
        best_test_acc = -1
        best_result = None
        for result in all_results:
            if result['code'] == code and result['test_accuracy'] > best_test_acc:
                best_test_acc = result['test_accuracy']
                best_result = result
        
        if best_result:
            print(f"\n  Best for {code}: {best_result['model_type']} with {best_result['encoding']} encoding")
            print(f"    Test accuracy: {best_result['test_accuracy']:.2f}% vs SOTA: {sota_acc:.1f}%")
            print(f"    Difference: {best_result['difference']:.2f}%")
    
    # Save all results
    results_df = pd.DataFrame(all_results)
    os.makedirs("../outputs", exist_ok=True)
    results_df.to_csv("../outputs/all_model_results.csv", index=False)
    print(f"\nAll results saved to ../outputs/all_model_results.csv")
    
    # Create summary of best models per benchmark
    best_results = []
    for code in selected_benchmarks:
        code_results = results_df[results_df['code'] == code]
        if len(code_results) > 0:
            best_idx = code_results['test_accuracy'].idxmax()
            best_results.append(results_df.loc[best_idx])
    
    best_df = pd.DataFrame(best_results)
    best_df.to_csv("../outputs/best_model_results.csv", index=False)
    print(f"Best results saved to ../outputs/best_model_results.csv")
    
    # Create visualization
    create_comparison_plot(best_df)
    
    return best_df

def create_comparison_plot(best_df):
    """Create visualization comparing best model accuracy vs SOTA"""
    plt.figure(figsize=(12, 6))
    
    # Set up bar positions
    x = np.arange(len(best_df))
    width = 0.35
    
    # Create bars
    plt.bar(x - width/2, best_df['test_accuracy'], width, label='Best Model (Test)', color='skyblue')
    plt.bar(x + width/2, best_df['sota_accuracy'], width, label='SOTA', color='lightcoral')
    
    # Add labels and title
    plt.xlabel('Benchmark')
    plt.ylabel('Accuracy (%)')
    plt.title('Best Model Test Accuracy vs SOTA for Selected Benchmarks')
    plt.xticks(x, best_df['code'])
    plt.legend()
    
    # Add value labels on bars
    for i, (test, sota) in enumerate(zip(best_df['test_accuracy'], best_df['sota_accuracy'])):
        plt.text(i - width/2, test + 0.5, f'{test:.1f}%', ha='center', va='bottom', fontsize=9)
        plt.text(i + width/2, sota + 0.5, f'{sota:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # Add model type annotation
        model_type = best_df.iloc[i]['model_type']
        encoding = best_df.iloc[i]['encoding']
        plt.text(i, -5, f'{model_type} ({encoding})', ha='center', va='top', fontsize=8, rotation=0)
    
    plt.ylim(0, max(max(best_df['test_accuracy']), max(best_df['sota_accuracy'])) + 10)
    plt.tight_layout()
    
    # Save figure
    os.makedirs("../report/images", exist_ok=True)
    plt.savefig("../report/images/best_accuracy_comparison.png", dpi=300)
    plt.close()
    
    print("Visualization saved to ../report/images/best_accuracy_comparison.png")

if __name__ == "__main__":
    best_df = main()
    print("\nBest Model Results:")
    print(best_df.to_string())