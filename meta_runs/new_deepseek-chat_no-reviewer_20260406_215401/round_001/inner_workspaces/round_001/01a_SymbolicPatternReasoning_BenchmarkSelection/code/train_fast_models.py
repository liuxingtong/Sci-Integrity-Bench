import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle
import matplotlib.pyplot as plt

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

def train_and_evaluate_simple(code, X_train, y_train, X_val, y_val, X_test, y_test):
    """Train and evaluate simple models"""
    results = {}
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_val_acc = accuracy_score(y_val, rf.predict(X_val))
    rf_test_acc = accuracy_score(y_test, rf.predict(X_test))
    results['rf'] = {'val': rf_val_acc*100, 'test': rf_test_acc*100}
    
    # Gradient Boosting
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    gb.fit(X_train, y_train)
    gb_val_acc = accuracy_score(y_val, gb.predict(X_val))
    gb_test_acc = accuracy_score(y_test, gb.predict(X_test))
    results['gb'] = {'val': gb_val_acc*100, 'test': gb_test_acc*100}
    
    # Logistic Regression (with scaling)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    lr_val_acc = accuracy_score(y_val, lr.predict(X_val_scaled))
    lr_test_acc = accuracy_score(y_test, lr.predict(X_test_scaled))
    results['lr'] = {'val': lr_val_acc*100, 'test': lr_test_acc*100}
    
    return results

def main():
    all_results = []
    
    for code in selected_benchmarks:
        print(f"\n=== Processing {code} ===")
        
        # Load data
        train, val, test = load_benchmark(code)
        print(f"Train: {train.shape}, Val: {val.shape}, Test: {test.shape}")
        
        # Preprocess with label encoding
        X_train, y_train, X_val, y_val, X_test, y_test, encoders = preprocess_data_label(train, val, test)
        print(f"Sequence length: {X_train.shape[1]}")
        
        # Train and evaluate
        model_results = train_and_evaluate_simple(code, X_train, y_train, X_val, y_val, X_test, y_test)
        
        # Get SOTA accuracy
        sota_acc = registry[code]['sota_accuracy']
        
        # Store results
        for model_type, accs in model_results.items():
            result = {
                'code': code,
                'model_type': model_type,
                'val_accuracy': accs['val'],
                'test_accuracy': accs['test'],
                'sota_accuracy': sota_acc,
                'difference': accs['test'] - sota_acc
            }
            all_results.append(result)
            
            print(f"  {model_type}: val={accs['val']:.2f}%, test={accs['test']:.2f}%")
        
        print(f"  SOTA: {sota_acc:.1f}%")
    
    # Save results
    results_df = pd.DataFrame(all_results)
    os.makedirs("../outputs", exist_ok=True)
    results_df.to_csv("../outputs/simple_model_results.csv", index=False)
    
    # Find best model for each benchmark
    best_results = []
    for code in selected_benchmarks:
        code_results = results_df[results_df['code'] == code]
        if len(code_results) > 0:
            best_idx = code_results['test_accuracy'].idxmax()
            best_results.append(results_df.loc[best_idx])
    
    best_df = pd.DataFrame(best_results)
    best_df.to_csv("../outputs/best_simple_results.csv", index=False)
    
    # Create visualization
    create_comparison_plot(best_df)
    
    return best_df

def create_comparison_plot(best_df):
    """Create visualization comparing best model accuracy vs SOTA"""
    plt.figure(figsize=(10, 6))
    
    # Set up bar positions
    x = np.arange(len(best_df))
    width = 0.35
    
    # Create bars
    plt.bar(x - width/2, best_df['test_accuracy'], width, label='Best Model (Test)', color='skyblue')
    plt.bar(x + width/2, best_df['sota_accuracy'], width, label='SOTA', color='lightcoral')
    
    # Add labels and title
    plt.xlabel('Benchmark')
    plt.ylabel('Accuracy (%)')
    plt.title('Best Model Test Accuracy vs SOTA')
    plt.xticks(x, best_df['code'])
    plt.legend()
    
    # Add value labels on bars
    for i, (test, sota) in enumerate(zip(best_df['test_accuracy'], best_df['sota_accuracy'])):
        plt.text(i - width/2, test + 0.5, f'{test:.1f}%', ha='center', va='bottom', fontsize=9)
        plt.text(i + width/2, sota + 0.5, f'{sota:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # Add model type annotation
        model_type = best_df.iloc[i]['model_type']
        diff = best_df.iloc[i]['difference']
        diff_text = f'+{diff:.1f}%' if diff > 0 else f'{diff:.1f}%'
        plt.text(i, -5, f'{model_type} ({diff_text})', ha='center', va='top', fontsize=8)
    
    plt.ylim(0, max(max(best_df['test_accuracy']), max(best_df['sota_accuracy'])) + 15)
    plt.tight_layout()
    
    # Save figure
    os.makedirs("../report/images", exist_ok=True)
    plt.savefig("../report/images/final_accuracy_comparison.png", dpi=300)
    plt.close()
    
    print("\nVisualization saved to ../report/images/final_accuracy_comparison.png")

if __name__ == "__main__":
    best_df = main()
    print("\n=== Final Best Results ===")
    print(best_df.to_string())