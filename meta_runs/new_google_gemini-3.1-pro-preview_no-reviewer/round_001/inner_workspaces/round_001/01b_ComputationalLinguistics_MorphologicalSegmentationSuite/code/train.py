import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import sacrebleu
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Define a simple sequence-to-sequence model for character-level segmentation
class CharSeq2Seq(nn.Module):
    def __init__(self, vocab_size, hidden_size=128):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.encoder = nn.LSTM(hidden_size, hidden_size, batch_first=True)
        self.decoder = nn.LSTM(hidden_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, vocab_size)
        
    def forward(self, src, trg):
        # src: (batch, seq_len)
        # trg: (batch, seq_len)
        embedded_src = self.embedding(src)
        _, (hidden, cell) = self.encoder(embedded_src)
        
        embedded_trg = self.embedding(trg)
        output, _ = self.decoder(embedded_trg, (hidden, cell))
        
        prediction = self.fc(output)
        return prediction

class MorphDataset(Dataset):
    def __init__(self, df, char2idx, max_len=100):
        self.df = df
        self.char2idx = char2idx
        self.max_len = max_len
        
    def __len__(self):
        return len(self.df)
        
    def __getitem__(self, idx):
        src = self.df.iloc[idx]['source']
        trg = self.df.iloc[idx]['target']
        
        src_idx = [self.char2idx.get(c, self.char2idx['<UNK>']) for c in src][:self.max_len-2]
        src_idx = [self.char2idx['<SOS>']] + src_idx + [self.char2idx['<EOS>']]
        
        trg_idx = [self.char2idx.get(c, self.char2idx['<UNK>']) for c in trg][:self.max_len-2]
        trg_idx = [self.char2idx['<SOS>']] + trg_idx + [self.char2idx['<EOS>']]
        
        # Pad
        src_idx += [self.char2idx['<PAD>']] * (self.max_len - len(src_idx))
        trg_idx += [self.char2idx['<PAD>']] * (self.max_len - len(trg_idx))
        
        return torch.tensor(src_idx), torch.tensor(trg_idx)

def build_vocab(dfs):
    chars = set()
    for df in dfs:
        for text in df['source'].tolist() + df['target'].tolist():
            chars.update(list(text))
    
    char2idx = {'<PAD>': 0, '<SOS>': 1, '<EOS>': 2, '<UNK>': 3}
    for c in sorted(list(chars)):
        if c not in char2idx:
            char2idx[c] = len(char2idx)
            
    idx2char = {i: c for c, i in char2idx.items()}
    return char2idx, idx2char

def train_model(model, train_loader, val_loader, epochs=50, lr=0.001, device='cpu'):
    criterion = nn.CrossEntropyLoss(ignore_index=0) # Ignore PAD
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    model.to(device)
    
    train_losses = []
    val_losses = []
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        for src, trg in train_loader:
            src, trg = src.to(device), trg.to(device)
            
            optimizer.zero_grad()
            
            # Teacher forcing: feed target as input to decoder
            # We shift target by 1 for input, and predict the original target
            trg_input = trg[:, :-1]
            trg_target = trg[:, 1:]
            
            output = model(src, trg_input)
            
            # output: (batch, seq_len, vocab_size)
            # trg_target: (batch, seq_len)
            loss = criterion(output.reshape(-1, output.shape[-1]), trg_target.reshape(-1))
            
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        train_losses.append(epoch_loss / len(train_loader))
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for src, trg in val_loader:
                src, trg = src.to(device), trg.to(device)
                trg_input = trg[:, :-1]
                trg_target = trg[:, 1:]
                output = model(src, trg_input)
                loss = criterion(output.reshape(-1, output.shape[-1]), trg_target.reshape(-1))
                val_loss += loss.item()
        val_losses.append(val_loss / len(val_loader))
        
    return train_losses, val_losses

def predict(model, src_tensor, idx2char, max_len=100, device='cpu'):
    model.eval()
    with torch.no_grad():
        src_tensor = src_tensor.unsqueeze(0).to(device)
        embedded_src = model.embedding(src_tensor)
        _, (hidden, cell) = model.encoder(embedded_src)
        
        trg_indexes = [1] # <SOS>
        
        for i in range(max_len):
            trg_tensor = torch.tensor([trg_indexes[-1]]).unsqueeze(0).to(device)
            embedded_trg = model.embedding(trg_tensor)
            output, (hidden, cell) = model.decoder(embedded_trg, (hidden, cell))
            
            pred_token = model.fc(output).argmax(2).item()
            trg_indexes.append(pred_token)
            
            if pred_token == 2: # <EOS>
                break
                
    trg_chars = [idx2char[i] for i in trg_indexes if i not in [0, 1, 2, 3]]
    return ''.join(trg_chars)

def evaluate(model, test_df, char2idx, idx2char, device='cpu'):
    predictions = []
    references = []
    
    for _, row in test_df.iterrows():
        src = row['source']
        trg = row['target']
        
        src_idx = [char2idx.get(c, char2idx['<UNK>']) for c in src][:100-2]
        src_idx = [char2idx['<SOS>']] + src_idx + [char2idx['<EOS>']]
        src_tensor = torch.tensor(src_idx)
        
        pred = predict(model, src_tensor, idx2char, device=device)
        predictions.append(pred)
        references.append([trg])
        
    chrf = sacrebleu.corpus_chrf(predictions, references)
    return chrf.score, predictions

def main():
    # Select 5 benchmarks
    # Let's pick a mix of script families and dev_bleu scores
    # KWP (Latin, low), ZTE (Arabic, low), HIB (Cyrillic, mid), VDN (Devanagari, high), DWN (Latin, high)
    benchmarks = ['KWP', 'ZTE', 'HIB', 'VDN', 'DWN']
    
    results = {}
    
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    for bm in benchmarks:
        print(f"\nTraining benchmark: {bm}")
        train_df = pd.read_csv(f'data/corpora/{bm}/train.csv')
        val_df = pd.read_csv(f'data/corpora/{bm}/val.csv')
        test_df = pd.read_csv(f'data/corpora/{bm}/test.csv')
        
        char2idx, idx2char = build_vocab([train_df, val_df, test_df])
        vocab_size = len(char2idx)
        
        train_dataset = MorphDataset(train_df, char2idx)
        val_dataset = MorphDataset(val_df, char2idx)
        
        train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=4)
        
        model = CharSeq2Seq(vocab_size).to(device)
        
        train_losses, val_losses = train_model(model, train_loader, val_loader, epochs=100, device=device)
        
        # Plot losses
        plt.figure(figsize=(8, 5))
        plt.plot(train_losses, label='Train Loss')
        plt.plot(val_losses, label='Val Loss')
        plt.title(f'Learning Curves - {bm}')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.savefig(f'report/images/loss_{bm}.png')
        plt.close()
        
        # Evaluate
        chrf_score, preds = evaluate(model, test_df, char2idx, idx2char, device=device)
        print(f"{bm} chrF++: {chrf_score:.2f}")
        
        results[bm] = {
            'chrf': chrf_score,
            'predictions': preds,
            'references': test_df['target'].tolist()
        }
        
    with open('outputs/results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    # Plot final results
    plt.figure(figsize=(10, 6))
    sns.barplot(x=list(results.keys()), y=[r['chrf'] for r in results.values()])
    plt.title('chrF++ Scores by Benchmark')
    plt.ylabel('chrF++')
    plt.ylim(0, 100)
    plt.savefig('report/images/chrf_scores.png')
    plt.close()

if __name__ == '__main__':
    main()
