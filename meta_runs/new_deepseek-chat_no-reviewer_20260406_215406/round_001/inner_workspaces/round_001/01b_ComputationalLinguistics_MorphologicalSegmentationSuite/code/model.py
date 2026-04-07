import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class CharVocab:
    def __init__(self, texts):
        # Build vocabulary from all texts
        chars = set()
        for text in texts:
            chars.update(text)
        
        # Special tokens
        self.pad_token = '<pad>'
        self.sos_token = '<sos>'
        self.eos_token = '<eos>'
        self.unk_token = '<unk>'
        
        special_tokens = [self.pad_token, self.sos_token, self.eos_token, self.unk_token]
        
        self.char2idx = {}
        self.idx2char = {}
        
        # Add special tokens first
        for i, token in enumerate(special_tokens):
            self.char2idx[token] = i
            self.idx2char[i] = token
        
        # Add all characters
        for char in sorted(chars):
            if char not in self.char2idx:
                idx = len(self.char2idx)
                self.char2idx[char] = idx
                self.idx2char[idx] = char
        
        self.vocab_size = len(self.char2idx)
        self.pad_idx = self.char2idx[self.pad_token]
        self.sos_idx = self.char2idx[self.sos_token]
        self.eos_idx = self.char2idx[self.eos_token]
        self.unk_idx = self.char2idx[self.unk_token]
    
    def encode(self, text, add_special=False):
        indices = []
        if add_special:
            indices.append(self.sos_idx)
        
        for char in text:
            indices.append(self.char2idx.get(char, self.unk_idx))
            
        if add_special:
            indices.append(self.eos_idx)
            
        return indices
    
    def decode(self, indices):
        chars = []
        for idx in indices:
            if idx == self.eos_idx:
                break
            if idx == self.pad_idx or idx == self.sos_idx:
                continue
            chars.append(self.idx2char.get(idx, self.unk_token))
        return ''.join(chars)

class Encoder(nn.Module):
    def __init__(self, vocab_size, embedding_dim=64, hidden_dim=128, num_layers=1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers=num_layers, 
                           batch_first=True, bidirectional=True)
        
    def forward(self, x):
        embedded = self.embedding(x)
        outputs, (hidden, cell) = self.lstm(embedded)
        # Combine bidirectional outputs
        outputs = outputs[:, :, :hidden.shape[-1]] + outputs[:, :, hidden.shape[-1]:]
        return outputs, (hidden, cell)

class Attention(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attn = nn.Linear(hidden_dim * 2, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)
        
    def forward(self, hidden, encoder_outputs):
        # hidden: [batch_size, hidden_dim]
        # encoder_outputs: [batch_size, seq_len, hidden_dim]
        batch_size = encoder_outputs.shape[0]
        src_len = encoder_outputs.shape[1]
        
        # Repeat hidden src_len times
        hidden_repeated = hidden.unsqueeze(1).repeat(1, src_len, 1)
        
        # Calculate attention energies
        energy = torch.tanh(self.attn(torch.cat((hidden_repeated, encoder_outputs), dim=2)))
        attention = self.v(energy).squeeze(2)
        
        return F.softmax(attention, dim=1)

class Decoder(nn.Module):
    def __init__(self, vocab_size, embedding_dim=64, hidden_dim=128, num_layers=1):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.attention = Attention(hidden_dim)
        self.lstm = nn.LSTM(embedding_dim + hidden_dim, hidden_dim, 
                           num_layers=num_layers, batch_first=True)
        self.fc_out = nn.Linear(hidden_dim * 2, vocab_size)
        
    def forward(self, x, hidden, cell, encoder_outputs):
        # x: [batch_size]
        # hidden, cell: [num_layers, batch_size, hidden_dim]
        # encoder_outputs: [batch_size, seq_len, hidden_dim]
        
        x = x.unsqueeze(1)  # [batch_size, 1]
        embedded = self.embedding(x)  # [batch_size, 1, embedding_dim]
        
        # Get attention weights
        attn_weights = self.attention(hidden[-1], encoder_outputs)  # [batch_size, src_len]
        attn_weights = attn_weights.unsqueeze(1)  # [batch_size, 1, src_len]
        
        # Apply attention to encoder outputs
        weighted = torch.bmm(attn_weights, encoder_outputs)  # [batch_size, 1, hidden_dim]
        
        # LSTM input
        lstm_input = torch.cat((embedded, weighted), dim=2)  # [batch_size, 1, embedding_dim + hidden_dim]
        
        # LSTM forward
        output, (hidden, cell) = self.lstm(lstm_input, (hidden, cell))
        
        # Prediction
        output = output.squeeze(1)  # [batch_size, hidden_dim]
        weighted = weighted.squeeze(1)  # [batch_size, hidden_dim]
        prediction = self.fc_out(torch.cat((output, weighted), dim=1))  # [batch_size, vocab_size]
        
        return prediction, hidden, cell, attn_weights.squeeze(1)

class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder
        
    def forward(self, src, trg, teacher_forcing_ratio=0.5):
        batch_size = src.shape[0]
        trg_len = trg.shape[1]
        trg_vocab_size = self.decoder.vocab_size
        
        # Tensor to store outputs
        outputs = torch.zeros(batch_size, trg_len, trg_vocab_size).to(src.device)
        
        # Encode source
        encoder_outputs, (hidden, cell) = self.encoder(src)
        
        # The encoder is bidirectional, need to convert to decoder dimensions
        # Sum bidirectional hidden states
        hidden = hidden.sum(dim=0).unsqueeze(0)  # [num_layers, batch_size, hidden_dim]
        cell = cell.sum(dim=0).unsqueeze(0)
        
        # First input to decoder is SOS token
        input = trg[:, 0]
        
        for t in range(1, trg_len):
            output, hidden, cell, _ = self.decoder(input, hidden, cell, encoder_outputs)
            outputs[:, t] = output
            
            # Teacher forcing
            teacher_force = np.random.random() < teacher_forcing_ratio
            top1 = output.argmax(1)
            input = trg[:, t] if teacher_force else top1
            
        return outputs
