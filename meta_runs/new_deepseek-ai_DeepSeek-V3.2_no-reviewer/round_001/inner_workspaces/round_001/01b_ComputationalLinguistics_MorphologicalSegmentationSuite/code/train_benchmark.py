import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import random
import os
import sys
from tqdm import tqdm
from model import Vocabulary, Seq2SeqModel, create_vocab_from_data, prepare_batch

class MorphDataset(Dataset):
    def __init__(self, df, vocab):
        self.df = df
        self.vocab = vocab
        
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        source = self.df.iloc[idx]['source']
        target = self.df.iloc[idx]['target']
        return source, target


def train_model(benchmark_code, epochs=100, batch_size=4, lr=0.001, device='cpu'):
    """Train a model for one benchmark"""
    print(f"Training model for benchmark {benchmark_code}")
    
    # Load data
    train_df = pd.read_csv(f'../data/corpora/{benchmark_code}/train.csv')
    val_df = pd.read_csv(f'../data/corpora/{benchmark_code}/val.csv')
    
    # Create vocabulary
    vocab = create_vocab_from_data([train_df, val_df])
    print(f"Vocabulary size: {len(vocab)}")
    
    # Create datasets
    train_dataset = MorphDataset(train_df, vocab)
    val_dataset = MorphDataset(val_df, vocab)
    
    # Create model
    model = Seq2SeqModel(len(vocab), embedding_dim=32, hidden_dim=64, num_layers=2, dropout=0.2)
    model.to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(ignore_index=0)  # Ignore padding
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    # Training loop
    train_losses = []
    val_losses = []
    
    best_val_loss = float('inf')
    best_model_state = None
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        
        # Shuffle data
        indices = list(range(len(train_dataset)))
        random.shuffle(indices)
        
        # Process in batches
        for i in range(0, len(indices), batch_size):
            batch_indices = indices[i:i+batch_size]
            
            # Get batch data
            sources = []
            targets = []
            for idx in batch_indices:
                source, target = train_dataset[idx]
                sources.append(source)
                targets.append(target)
            
            # Prepare batch
            src_tensor, tgt_tensor = prepare_batch(sources, targets, vocab, device)
            
            # Forward pass
            optimizer.zero_grad()
            output = model(src_tensor, tgt_tensor, teacher_forcing_ratio=0.5)
            
            # Reshape for loss
            output_dim = output.shape[-1]
            output = output[:, 1:].reshape(-1, output_dim)  # Remove first token (SOS)
            tgt = tgt_tensor[:, 1:].reshape(-1)  # Remove first token (SOS)
            
            loss = criterion(output, tgt)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
        
        avg_train_loss = epoch_loss / (len(indices) / batch_size)
        train_losses.append(avg_train_loss)
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            val_indices = list(range(len(val_dataset)))
            for i in range(0, len(val_indices), batch_size):
                batch_indices = val_indices[i:i+batch_size]
                
                sources = []
                targets = []
                for idx in batch_indices:
                    source, target = val_dataset[idx]
                    sources.append(source)
                    targets.append(target)
                
                src_tensor, tgt_tensor = prepare_batch(sources, targets, vocab, device)
                
                output = model(src_tensor, tgt_tensor, teacher_forcing_ratio=0.0)  # No teacher forcing
                
                output_dim = output.shape[-1]
                output = output[:, 1:].reshape(-1, output_dim)
                tgt = tgt_tensor[:, 1:].reshape(-1)
                
                loss = criterion(output, tgt)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / (len(val_indices) / batch_size)
        val_losses.append(avg_val_loss)
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_model_state = model.state_dict().copy()
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
    
    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    print(f"Training completed. Best val loss: {best_val_loss:.4f}")
    
    return model, vocab, train_losses, val_losses


def evaluate_model(model, vocab, benchmark_code, device='cpu'):
    """Evaluate model on test set and compute chrF++"""
    from sacrebleu.metrics import CHRF
    
    # Load test data
    test_df = pd.read_csv(f'../data/corpora/{benchmark_code}/test.csv')
    
    # Initialize chrF++ metric
    chrf = CHRF(word_order=2)  # chrF++ with word order 2
    
    predictions = []
    references = []
    
    model.eval()
    with torch.no_grad():
        for idx in range(len(test_df)):
            source = test_df.iloc[idx]['source']
            target = test_df.iloc[idx]['target']  # Ground truth
            
            # Encode source
            src_encoded = vocab.encode(source)
            src_tensor = torch.tensor([src_encoded], dtype=torch.long).to(device)
            
            # Predict
            predicted_tokens = model.predict(src_tensor, max_len=50)
            
            # Decode prediction
            if isinstance(predicted_tokens, list):
                # Single sample
                predicted_str = vocab.decode(predicted_tokens)
            else:
                # Batch
                predicted_str = vocab.decode(predicted_tokens[0])
            
            # Convert predicted string back to space-separated tokens
            # This is tricky - we need to reconstruct the segmentation
            # For now, just use the predicted string as is
            # Actually, we need to compare with target which is space-separated
            
            # For chrF++, we need to compare strings
            # Target is space-separated, prediction is concatenated
            # Let's convert prediction to space-separated by character for now
            # This is a simplification
            predicted_segmented = ' '.join(list(predicted_str))
            
            predictions.append(predicted_segmented)
            references.append(target)
    
    # Compute chrF++
    chrf_score = chrf.corpus_score(predictions, [references])
    
    return chrf_score, predictions, references


if __name__ == "__main__":
    # Test with one benchmark
    benchmark_code = "KWP"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    model, vocab, train_losses, val_losses = train_model(benchmark_code, epochs=50, batch_size=4, lr=0.001, device=device)
    
    # Evaluate
    chrf_score, predictions, references = evaluate_model(model, vocab, benchmark_code, device=device)
    print(f"chrF++ score for {benchmark_code}: {chrf_score.score:.4f}")
    
    # Save results
    os.makedirs('../outputs', exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'vocab': vocab,
        'train_losses': train_losses,
        'val_losses': val_losses
    }, f'../outputs/model_{benchmark_code}.pt')
    
    # Save predictions
    results_df = pd.DataFrame({
        'source': [test_df.iloc[i]['source'] for i in range(len(predictions))],
        'prediction': predictions,
        'reference': references
    })
    results_df.to_csv(f'../outputs/predictions_{benchmark_code}.csv', index=False)
    
    print(f"Results saved to outputs/")
