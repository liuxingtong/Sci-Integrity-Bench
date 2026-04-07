import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

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

def preprocess_data(train, val, test):
    """Preprocess data: encode categorical tokens"""
    # Identify token columns
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
        # Fit on all data
        le.fit(all_data[col])
        
        # Transform each split
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

def train_and_evaluate(code, X_train, y_train, X_val, y_val, X_test, y_test):
    """Train Random Forest with hyperparameter tuning on validation set"""
    
    # Hyperparameter grid
    n_estimators_list = [50, 100, 200]
    max_depth_list = [5, 10, 20, None]
    
    best_val_acc = 0
    best_model = None
    best_params = {}
    
    for n_estimators in n_estimators_list:
        for max_depth in max_depth_list:
            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train, y_train)
            
            # Predict on validation
            y_val_pred = model.predict(X_val)
            val_acc = accuracy_score(y_val, y_val_pred)
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model = model
                best_params = {'n_estimators': n_estimators, 'max_depth': max_depth}
    
    # Evaluate on test set with best model
    y_test_pred = best_model.predict(X_test)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    return best_model, best_params, best_val_acc, test_acc

def main():
    results = []
    
    for code in selected_benchmarks:
        print(f"\n=== Processing {code} ===")
        
        # Load data
        train, val, test = load_benchmark(code)
        print(f"Train: {train.shape}, Val: {val.shape}, Test: {test.shape}")
        
        # Preprocess
        X_train, y_train, X_val, y_val, X_test, y_test, encoders = preprocess_data(train, val, test)
        print(f"Sequence length: {X_train.shape[1]}")
        
        # Train and evaluate
        model, params, val_acc, test_acc = train_and_evaluate(
            code, X_train, y_train, X_val, y_val, X_test, y_test
        )
        
        # Get SOTA accuracy
        sota_acc = registry[code]['sota_accuracy']
        
        # Store results
        result = {
            'code': code,
            'sequence_length': X_train.shape[1],
            'train_size': len(train),
            'val_size': len(val),
            'test_size': len(test),
            'best_params': params,
            'val_accuracy': val_acc * 100,
            'test_accuracy': test_acc * 100,
            'sota_accuracy': sota_acc,
            'difference': (test_acc * 100) - sota_acc
        }
        results.append(result)
        
        print(f"Best params: {params}")
        print(f"Val accuracy: {val_acc*100:.2f}%")
        print(f"Test accuracy: {test_acc*100:.2f}%")
        print(f"SOTA accuracy: {sota_acc:.1f}%")
        print(f"Difference: {(test_acc*100) - sota_acc:.2f}%")
        
        # Save model
        os.makedirs(f"../outputs/models/{code}", exist_ok=True)
        with open(f"../outputs/models/{code}/model.pkl", "wb") as f:
            pickle.dump(model, f)
        
        # Save encoders
        with open(f"../outputs/models/{code}/encoders.pkl", "wb") as f:
            pickle.dump(encoders, f)
    
    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv("../outputs/model_results.csv", index=False)
    print(f"\nResults saved to ../outputs/model_results.csv")
    
    # Create visualization
    create_visualization(results_df)
    
    return results_df

def create_visualization(results_df):
    """Create visualization comparing test accuracy vs SOTA"""
    plt.figure(figsize=(10, 6))
    
    # Set up bar positions
    x = np.arange(len(results_df))
    width = 0.35
    
    # Create bars
    plt.bar(x - width/2, results_df['test_accuracy'], width, label='Our Model (Test)', color='skyblue')
    plt.bar(x + width/2, results_df['sota_accuracy'], width, label='SOTA', color='lightcoral')
    
    # Add labels and title
    plt.xlabel('Benchmark')
    plt.ylabel('Accuracy (%)')
    plt.title('Test Accuracy vs SOTA for Selected Benchmarks')
    plt.xticks(x, results_df['code'])
    plt.legend()
    
    # Add value labels on bars
    for i, (test, sota) in enumerate(zip(results_df['test_accuracy'], results_df['sota_accuracy'])):
        plt.text(i - width/2, test + 0.5, f'{test:.1f}%', ha='center', va='bottom', fontsize=9)
        plt.text(i + width/2, sota + 0.5, f'{sota:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Save figure
    os.makedirs("../report/images", exist_ok=True)
    plt.savefig("../report/images/accuracy_comparison.png", dpi=300)
    plt.close()
    
    print("Visualization saved to ../report/images/accuracy_comparison.png")

if __name__ == "__main__":
    results_df = main()
    print("\nFinal Results:")
    print(results_df.to_string())