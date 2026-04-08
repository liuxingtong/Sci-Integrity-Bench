import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from collections import defaultdict
import random

class Vocabulary:
    def __init__(self):
        self.char2idx = {'<PAD>': 0, '<SOS>': 1, '<EOS>': 2}
        self.idx2char = {0: '<PAD>', 1: '<SOS>', 2: '<EOS>'}
        self.next_idx = 3
        
    def add_char(self, char):
        if char not in self.char2idx:
            self.char2idx[char] = self.next_idx
            self.idx2char[self.next_idx] = char
            self.next_idx += 1
            
    def add_string(self, string):
        for char in string:
            self.add_char(char)
            
    def encode(self, string, add_special=False):
        indices = [self.char2idx[char] for char in string]
        if add_special:
            indices = [self.char2idx['<SOS>']] + indices + [self.char2idx['<EOS>']]
        return indices
    
    def decode(self, indices):
        chars = []
        for idx in indices:
            if idx == self.char2idx['<EOS>']:
                break
            if idx != self.char2idx['<SOS>'] and idx != self.char2idx['<PAD>']:
                chars.append(self.idx2char[idx])
        return ''.join(chars)
    
    def __len__(self):
        return len(self.char2idx)


class SimpleSeq2Seq(nn.Module):
    def __init__(self, vocab_size, embedding_dim=32, hidden_dim=64, num_layers=1, dropout=0.2):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.vocab_size = vocab_size
        
        # Encoder
        self.encoder_embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.encoder_lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers=num_layers, 
                                    batch_first=True, dropout=dropout if num_layers > 1 else 0)
        
        # Decoder
        self.decoder_embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.decoder_lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers=num_layers,
                                    batch_first=True, dropout=dropout if num_layers > 1 else 0)
        
        # Output projection
        self.output_linear = nn.Linear(hidden_dim, vocab_size)
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, src, tgt, teacher_forcing_ratio=0.5):
        # src: [batch, src_len]
        # tgt: [batch, tgt_len]
        batch_size = src.size(0)
        src_len = src.size(1)
        tgt_len = tgt.size(1)
        
        # Encode source
        src_embedded = self.dropout(self.encoder_embedding(src))  # [batch, src_len, emb]
        _, (hidden, cell) = self.encoder_lstm(src_embedded)
        # hidden, cell: [num_layers, batch, hidden]
        
        # Prepare for decoding
        decoder_input = tgt[:, 0].unsqueeze(1)  # First token is SOS
        outputs = torch.zeros(batch_size, tgt_len, self.vocab_size).to(src.device)
        
        for t in range(1, tgt_len):
            # Decode step
            decoder_embedded = self.dropout(self.decoder_embedding(decoder_input))  # [batch, 1, emb]
            
            # LSTM step
            decoder_output, (hidden, cell) = self.decoder_lstm(decoder_embedded, (hidden, cell))
            
            # Output projection
            output = self.output_linear(decoder_output.squeeze(1))  # [batch, vocab_size]
            outputs[:, t, :] = output
            
            # Teacher forcing
            teacher_force = random.random() < teacher_forcing_ratio
            if teacher_force and t < tgt_len - 1:
                decoder_input = tgt[:, t].unsqueeze(1)
            else:
                top1 = output.argmax(1)
                decoder_input = top1.unsqueeze(1)
                
        return outputs
    
    def predict(self, src, max_len=50):
        self.eval()
        with torch.no_grad():
            batch_size = src.size(0)
            
            # Encode source
            src_embedded = self.encoder_embedding(src)
            _, (hidden, cell) = self.encoder_lstm(src_embedded)
            
            # Start with SOS
            decoder_input = torch.tensor([[1]] * batch_size).to(src.device)  # SOS token
            decoded_tokens = []
            
            for t in range(max_len):
                decoder_embedded = self.decoder_embedding(decoder_input)
                
                decoder_output, (hidden, cell) = self.decoder_lstm(decoder_embedded, (hidden, cell))
                
                output = self.output_linear(decoder_output.squeeze(1))
                
                top1 = output.argmax(1)
                decoded_tokens.append(top1.item() if batch_size == 1 else top1.cpu().numpy())
                
                decoder_input = top1.unsqueeze(1)
                
                # Stop if EOS
                if top1.item() == 2:  # EOS token
                    break
                    
        return decoded_tokens


def create_vocab_from_data(dataframes):
    """Create vocabulary from multiple dataframes"""
    vocab = Vocabulary()
    for df in dataframes:
        for source in df['source']:
            vocab.add_string(source)
        for target in df['target']:
            # Target has spaces, we need to add each character in tokens
            tokens = target.split()
            for token in tokens:
                vocab.add_string(token)
    return vocab


def prepare_batch(sources, targets, vocab, device='cpu'):
    """Prepare batch for training"""
    # Encode sources
    src_encoded = [vocab.encode(src) for src in sources]
    src_lens = [len(seq) for seq in src_encoded]
    max_src_len = max(src_lens)
    
    # Pad sources
    src_padded = []
    for seq in src_encoded:
        padded = seq + [0] * (max_src_len - len(seq))
        src_padded.append(padded)
    
    # Encode targets (with SOS/EOS)
    tgt_encoded = []
    for target in targets:
        # Target is space-separated tokens
        tokens = target.split()
        # Join tokens to get string, then encode
        target_str = ''.join(tokens)
        tgt_encoded.append(vocab.encode(target_str, add_special=True))
    
    tgt_lens = [len(seq) for seq in tgt_encoded]
    max_tgt_len = max(tgt_lens)
    
    # Pad targets
    tgt_padded = []
    for seq in tgt_encoded:
        padded = seq + [0] * (max_tgt_len - len(seq))
        tgt_padded.append(padded)
    
    src_tensor = torch.tensor(src_padded, dtype=torch.long).to(device)
    tgt_tensor = torch.tensor(tgt_padded, dtype=torch.long).to(device)
    
    return src_tensor, tgt_tensor
