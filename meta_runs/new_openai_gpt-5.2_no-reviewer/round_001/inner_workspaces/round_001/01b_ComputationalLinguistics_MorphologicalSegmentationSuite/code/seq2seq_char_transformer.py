"""Character-level Transformer seq2seq for morphological segmentation.

This module implements:
- CharVocab: builds character vocab from training data
- TransformerSeq2Seq: encoder-decoder using torch.nn.Transformer
- training loop with teacher forcing
- greedy decoding

Designed to be lightweight and fully offline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Iterable, Optional

import torch
import torch.nn as nn


SPECIAL_TOKENS = {
    "pad": "<pad>",
    "bos": "<bos>",
    "eos": "<eos>",
    "unk": "<unk>",
}


class CharVocab:
    def __init__(self, stoi: Dict[str, int]):
        self.stoi = dict(stoi)
        self.itos = {i: s for s, i in self.stoi.items()}
        self.pad_id = self.stoi[SPECIAL_TOKENS["pad"]]
        self.bos_id = self.stoi[SPECIAL_TOKENS["bos"]]
        self.eos_id = self.stoi[SPECIAL_TOKENS["eos"]]
        self.unk_id = self.stoi[SPECIAL_TOKENS["unk"]]

    @classmethod
    def build(cls, texts: Iterable[str], extra_tokens: Optional[List[str]] = None) -> "CharVocab":
        chars = set()
        for t in texts:
            chars.update(list(t))
        base = [SPECIAL_TOKENS["pad"], SPECIAL_TOKENS["bos"], SPECIAL_TOKENS["eos"], SPECIAL_TOKENS["unk"]]
        if extra_tokens:
            for tok in extra_tokens:
                if tok not in base:
                    base.append(tok)
        # stable ordering for reproducibility
        char_list = sorted(chars)
        all_tokens = base + [c for c in char_list if c not in base]
        stoi = {s: i for i, s in enumerate(all_tokens)}
        return cls(stoi)

    def encode(self, s: str, add_bos: bool = False, add_eos: bool = False) -> List[int]:
        ids = []
        if add_bos:
            ids.append(self.bos_id)
        for ch in s:
            ids.append(self.stoi.get(ch, self.unk_id))
        if add_eos:
            ids.append(self.eos_id)
        return ids

    def decode(self, ids: List[int], stop_at_eos: bool = True, skip_special: bool = True) -> str:
        out = []
        for i in ids:
            if stop_at_eos and i == self.eos_id:
                break
            tok = self.itos.get(int(i), SPECIAL_TOKENS["unk"])
            if skip_special and tok in SPECIAL_TOKENS.values():
                continue
            out.append(tok)
        return "".join(out)


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 512):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq, d_model)
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class TransformerSeq2Seq(nn.Module):
    def __init__(
        self,
        src_vocab_size: int,
        tgt_vocab_size: int,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 256,
        dropout: float = 0.1,
        max_len: int = 256,
        pad_id: int = 0,
    ):
        super().__init__()
        self.pad_id = pad_id
        self.d_model = d_model

        self.src_embed = nn.Embedding(src_vocab_size, d_model, padding_idx=pad_id)
        self.tgt_embed = nn.Embedding(tgt_vocab_size, d_model, padding_idx=pad_id)
        self.pos = PositionalEncoding(d_model, dropout=dropout, max_len=max_len)

        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=nhead,
            num_encoder_layers=num_layers,
            num_decoder_layers=num_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.out = nn.Linear(d_model, tgt_vocab_size)

    def make_src_key_padding_mask(self, src: torch.Tensor) -> torch.Tensor:
        # (batch, src_len)
        return src.eq(self.pad_id)

    def make_tgt_key_padding_mask(self, tgt: torch.Tensor) -> torch.Tensor:
        return tgt.eq(self.pad_id)

    def make_tgt_subsequent_mask(self, tgt_len: int, device) -> torch.Tensor:
        # (tgt_len, tgt_len) bool mask: True = disallow attending
        return torch.triu(torch.ones(tgt_len, tgt_len, device=device, dtype=torch.bool), diagonal=1)

    def forward(self, src: torch.Tensor, tgt_inp: torch.Tensor) -> torch.Tensor:
        # src: (batch, src_len) ; tgt_inp: (batch, tgt_len)
        src_key_padding_mask = self.make_src_key_padding_mask(src)
        tgt_key_padding_mask = self.make_tgt_key_padding_mask(tgt_inp)
        tgt_mask = self.make_tgt_subsequent_mask(tgt_inp.size(1), device=tgt_inp.device)

        src_emb = self.pos(self.src_embed(src) * math.sqrt(self.d_model))
        tgt_emb = self.pos(self.tgt_embed(tgt_inp) * math.sqrt(self.d_model))

        hs = self.transformer(
            src_emb,
            tgt_emb,
            tgt_mask=tgt_mask,
            src_key_padding_mask=src_key_padding_mask,
            tgt_key_padding_mask=tgt_key_padding_mask,
            memory_key_padding_mask=src_key_padding_mask,
        )
        logits = self.out(hs)  # (batch, tgt_len, vocab)
        return logits

    @torch.no_grad()
    def greedy_decode(
        self,
        src: torch.Tensor,
        bos_id: int,
        eos_id: int,
        max_len: int,
    ) -> torch.Tensor:
        self.eval()
        device = src.device
        src_key_padding_mask = self.make_src_key_padding_mask(src)
        src_emb = self.pos(self.src_embed(src) * math.sqrt(self.d_model))
        memory = self.transformer.encoder(src_emb, src_key_padding_mask=src_key_padding_mask)

        ys = torch.full((src.size(0), 1), bos_id, dtype=torch.long, device=device)
        finished = torch.zeros((src.size(0),), dtype=torch.bool, device=device)
        for _ in range(max_len - 1):
            tgt_mask = self.make_tgt_subsequent_mask(ys.size(1), device=device)
            tgt_emb = self.pos(self.tgt_embed(ys) * math.sqrt(self.d_model))
            out = self.transformer.decoder(
                tgt_emb,
                memory,
                tgt_mask=tgt_mask,
                memory_key_padding_mask=src_key_padding_mask,
            )
            logits = self.out(out[:, -1, :])
            next_token = torch.argmax(logits, dim=-1).unsqueeze(1)
            ys = torch.cat([ys, next_token], dim=1)
            finished |= next_token.squeeze(1).eq(eos_id)
            if bool(finished.all()):
                break
        return ys


@dataclass
class Batch:
    src: torch.Tensor
    tgt_inp: torch.Tensor
    tgt_out: torch.Tensor


def pad_sequences(seqs: List[List[int]], pad_id: int) -> torch.Tensor:
    max_len = max(len(s) for s in seqs)
    out = torch.full((len(seqs), max_len), pad_id, dtype=torch.long)
    for i, s in enumerate(seqs):
        out[i, : len(s)] = torch.tensor(s, dtype=torch.long)
    return out


def make_batches(
    pairs: List[Tuple[List[int], List[int]]],
    pad_id: int,
    batch_size: int,
    shuffle: bool,
    device: torch.device,
) -> Iterable[Batch]:
    idx = torch.randperm(len(pairs)).tolist() if shuffle else list(range(len(pairs)))
    for start in range(0, len(idx), batch_size):
        batch_idx = idx[start : start + batch_size]
        src_seqs = [pairs[i][0] for i in batch_idx]
        tgt_full = [pairs[i][1] for i in batch_idx]
        # tgt_inp excludes last; tgt_out excludes first
        tgt_inp = [t[:-1] for t in tgt_full]
        tgt_out = [t[1:] for t in tgt_full]
        b = Batch(
            src=pad_sequences(src_seqs, pad_id).to(device),
            tgt_inp=pad_sequences(tgt_inp, pad_id).to(device),
            tgt_out=pad_sequences(tgt_out, pad_id).to(device),
        )
        yield b
