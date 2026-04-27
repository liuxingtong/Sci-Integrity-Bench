# Baseline training script for cell patch segmentation benchmarks
# Reproducible single-run training per dataset with fixed architecture (small U-Net)

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset


# -----------------------------
# Utils: column parsing / loading
# -----------------------------

def _try_int_suffix(col: str):
    """Extract a sortable integer key from a column name.

    Supports: 'img_12', 'mask_12', '12', 'x12', 'pixel12', etc.
    Falls back to lexical.
    """
    s = str(col)
    if s.isdigit():
        return (0, int(s))
    import re

    m = re.search(r"(\d+)(?!.*\d)", s)
    if m:
        return (0, int(m.group(1)))
    return (1, s)


def _infer_image_mask_columns(df_head: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    """Infer (image_cols, mask_cols, meta_cols) from a dataframe (small head is OK).

    Strategy:
    1) Prefer name-based detection for mask columns ('mask'/'y'/'target').
    2) Otherwise, use binary-valued columns on the head and select the largest group
       that forms a perfect square count as mask.
    3) Meta columns are non-image/non-mask; kept but ignored.

    Assumption: mask pixels are 0/1.
    """

    cols = list(df_head.columns)
    lower = [c.lower() for c in cols]

    # Name-based
    mask_cols = [c for c, lc in zip(cols, lower) if ("mask" in lc) or lc.startswith("y") or ("target" in lc)]

    if mask_cols:
        # Image columns: all numeric pixel-like columns that are not mask
        image_cols = [c for c in cols if c not in mask_cols]
        meta_cols = []
        return image_cols, mask_cols, meta_cols

    # Binary-value-based
    binary_cols = []
    for c in cols:
        v = df_head[c].to_numpy()
        v = v[np.isfinite(v)]
        u = np.unique(v)
        if len(u) <= 2 and set(u).issubset({0, 1}):
            binary_cols.append(c)

    # Try to use contiguous block at the end (common layout: image..., mask...)
    if binary_cols:
        idx = [cols.index(c) for c in binary_cols]
        # If most binary cols are near the end, take the trailing run as mask
        # Build trailing run
        trailing = []
        for c in reversed(cols):
            if c in binary_cols:
                trailing.append(c)
            else:
                if trailing:
                    break
        trailing = list(reversed(trailing))

        def is_square(n: int) -> bool:
            r = int(round(math.sqrt(n)))
            return r * r == n

        if is_square(len(trailing)) and len(trailing) >= 16:
            mask_cols = trailing
        else:
            # Fallback: choose largest square-sized subset among binary columns
            # Prefer largest n that is a perfect square
            n = len(binary_cols)
            sq = int(math.floor(math.sqrt(n)))
            mask_n = sq * sq
            mask_cols = sorted(binary_cols, key=_try_int_suffix)[:mask_n]

    else:
        raise RuntimeError("Could not infer mask columns (no name hints, no binary columns in head).")

    image_cols = [c for c in cols if c not in mask_cols]

    # Meta detection: if remaining count is not divisible by mask pixels, likely meta exists.
    # We'll attempt to separate meta by looking for low-variance integer-ish columns.
    # But for simplicity, keep image_cols as all non-mask; we'll later validate reshape.
    meta_cols = []

    return image_cols, mask_cols, meta_cols


def load_split(dataset_id: str, split: str) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """Load one split (train/val/test) into (X, Y) arrays with shapes:
        X: (N, C, H, W) float32
        Y: (N, 1, H, W) float32 {0,1}

    Returns also a dict with inferred info.
    """
    path = Path("data") / "patches" / dataset_id / f"{split}.csv"
    if not path.exists():
        raise FileNotFoundError(path)

    # Read small head for schema inference
    df_head = pd.read_csv(path, nrows=50)
    image_cols, mask_cols, meta_cols = _infer_image_mask_columns(df_head)

    # Sort columns by numeric suffix if possible (helps consistent spatial ordering)
    image_cols_sorted = sorted(image_cols, key=_try_int_suffix)
    mask_cols_sorted = sorted(mask_cols, key=_try_int_suffix)

    # Load full split but only the relevant columns (keeps memory down)
    usecols = image_cols_sorted + mask_cols_sorted
    df = pd.read_csv(path, usecols=usecols)

    X_flat = df[image_cols_sorted].to_numpy(dtype=np.float32)
    Y_flat = df[mask_cols_sorted].to_numpy(dtype=np.float32)

    n = X_flat.shape[0]
    p = Y_flat.shape[1]
    s = int(round(math.sqrt(p)))
    if s * s != p:
        raise RuntimeError(f"Mask pixel count not square: {p}")

    # Infer channels
    if X_flat.shape[1] % p != 0:
        # Attempt to drop possible meta columns from image_cols (rare)
        # Heuristic: remove a small number of columns from the front until divisible.
        for drop in range(1, 11):
            if (X_flat.shape[1] - drop) % p == 0:
                X_flat = X_flat[:, drop:]
                image_cols_sorted = image_cols_sorted[drop:]
                break
        if X_flat.shape[1] % p != 0:
            raise RuntimeError(
                f"Image column count {X_flat.shape[1]} not divisible by mask pixels {p}. "
                "Unable to infer channels." 
            )

    c = X_flat.shape[1] // p
    X = X_flat.reshape(n, c, s, s)
    Y = Y_flat.reshape(n, 1, s, s)

    info = {
        "dataset_id": dataset_id,
        "split": split,
        "n": int(n),
        "H": int(s),
        "W": int(s),
        "C": int(c),
        "n_image_cols": int(len(image_cols_sorted)),
        "n_mask_cols": int(len(mask_cols_sorted)),
    }
    return X, Y, info


# -----------------------------
# Torch Dataset
# -----------------------------


class NumpySegDataset(Dataset):
    def __init__(self, X: np.ndarray, Y: np.ndarray):
        self.X = torch.from_numpy(X)
        self.Y = torch.from_numpy(Y)

    def __len__(self):
        return self.X.shape[0]

    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]


# -----------------------------
# Model: small U-Net
# -----------------------------


def conv_block(in_ch: int, out_ch: int):
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_ch, out_ch, 3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


class SmallUNet(nn.Module):
    def __init__(self, in_ch: int, base: int = 16):
        super().__init__()
        self.enc1 = conv_block(in_ch, base)
        self.pool1 = nn.MaxPool2d(2)
        self.enc2 = conv_block(base, base * 2)
        self.pool2 = nn.MaxPool2d(2)
        self.enc3 = conv_block(base * 2, base * 4)

        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.dec2 = conv_block(base * 4, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.dec1 = conv_block(base * 2, base)

        self.out = nn.Conv2d(base, 1, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))

        d2 = self.up2(e3)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        return self.out(d1)


# -----------------------------
# Metrics / Loss
# -----------------------------


def dice_from_logits(logits: torch.Tensor, y: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    """Mean Dice over batch, thresholded at 0.5."""
    p = (torch.sigmoid(logits) > 0.5).float()
    y = (y > 0.5).float()
    # sum over spatial dims
    inter = (p * y).sum(dim=(1, 2, 3))
    den = p.sum(dim=(1, 2, 3)) + y.sum(dim=(1, 2, 3))
    dice = (2 * inter + eps) / (den + eps)
    return dice.mean()


def soft_dice_loss(logits: torch.Tensor, y: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    p = torch.sigmoid(logits)
    y = y.float()
    inter = (p * y).sum(dim=(1, 2, 3))
    den = p.sum(dim=(1, 2, 3)) + y.sum(dim=(1, 2, 3))
    dice = (2 * inter + eps) / (den + eps)
    return 1 - dice.mean()


# -----------------------------
# Training
# -----------------------------


@dataclass
class TrainConfig:
    epochs: int = 40
    batch_size: int = 32
    lr: float = 1e-3
    weight_decay: float = 1e-4
    patience: int = 7
    seed: int = 0


def set_seed(seed: int):
    import random

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> Dict[str, float]:
    model.eval()
    dices = []
    bces = []
    for x, y in loader:
        x = x.to(device)
        y = y.to(device)
        logits = model(x)
        dices.append(dice_from_logits(logits, y).item())
        bces.append(F.binary_cross_entropy_with_logits(logits, y).item())
    return {
        "dice": float(np.mean(dices)) if dices else float("nan"),
        "bce": float(np.mean(bces)) if bces else float("nan"),
    }


def train_one_dataset(dataset_id: str, cfg: TrainConfig, out_dir: Path) -> Dict:
    set_seed(cfg.seed)

    Xtr, Ytr, info_tr = load_split(dataset_id, "train")
    Xva, Yva, info_va = load_split(dataset_id, "val")
    Xte, Yte, info_te = load_split(dataset_id, "test")

    assert info_tr["H"] == info_va["H"] == info_te["H"]
    assert info_tr["W"] == info_va["W"] == info_te["W"]
    assert info_tr["C"] == info_va["C"] == info_te["C"]

    # Normalize using train stats
    mu = Xtr.mean(axis=(0, 2, 3), keepdims=True)
    sd = Xtr.std(axis=(0, 2, 3), keepdims=True) + 1e-6
    Xtr = (Xtr - mu) / sd
    Xva = (Xva - mu) / sd
    Xte = (Xte - mu) / sd

    ds_tr = NumpySegDataset(Xtr, Ytr)
    ds_va = NumpySegDataset(Xva, Yva)
    ds_te = NumpySegDataset(Xte, Yte)

    loader_tr = DataLoader(ds_tr, batch_size=cfg.batch_size, shuffle=True, num_workers=0)
    loader_va = DataLoader(ds_va, batch_size=cfg.batch_size, shuffle=False, num_workers=0)
    loader_te = DataLoader(ds_te, batch_size=cfg.batch_size, shuffle=False, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = SmallUNet(in_ch=info_tr["C"], base=16).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    history = []
    best_val = -1
    best_state = None
    bad = 0

    for epoch in range(1, cfg.epochs + 1):
        model.train()
        losses = []
        dices = []
        for x, y in loader_tr:
            x = x.to(device)
            y = y.to(device)
            opt.zero_grad(set_to_none=True)
            logits = model(x)
            loss = 0.5 * F.binary_cross_entropy_with_logits(logits, y) + 0.5 * soft_dice_loss(logits, y)
            loss.backward()
            opt.step()
            losses.append(loss.item())
            dices.append(dice_from_logits(logits.detach(), y).item())

        tr_loss = float(np.mean(losses))
        tr_dice = float(np.mean(dices))
        va = evaluate(model, loader_va, device)

        rec = {
            "epoch": epoch,
            "train_loss": tr_loss,
            "train_dice": tr_dice,
            "val_dice": va["dice"],
            "val_bce": va["bce"],
        }
        history.append(rec)

        if va["dice"] > best_val + 1e-4:
            best_val = va["dice"]
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
            bad = 0
        else:
            bad += 1
            if bad >= cfg.patience:
                break

    # Load best state
    if best_state is not None:
        model.load_state_dict(best_state)

    va_best = evaluate(model, loader_va, device)
    te = evaluate(model, loader_te, device)

    # Save artifacts
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(),
        "mu": mu,
        "sd": sd,
        "info": info_tr,
        "cfg": cfg.__dict__,
    }, out_dir / f"{dataset_id}_model.pt")

    with open(out_dir / f"{dataset_id}_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    result = {
        "dataset_id": dataset_id,
        "info": info_tr,
        "train": {"n": int(Xtr.shape[0])},
        "val": {"n": int(Xva.shape[0]), **va_best},
        "test": {"n": int(Xte.shape[0]), **te},
        "best_val_dice": float(best_val),
        "epochs_ran": int(history[-1]["epoch"]) if history else 0,
        "device": str(device),
    }

    with open(out_dir / f"{dataset_id}_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def pick_datasets(registry_path: str, k: int = 4) -> List[str]:
    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    df = pd.DataFrame(reg)

    # Ensure expected fields
    for col in ["dataset_id", "published_dice_sota", "train_patches", "positive_pixel_rate"]:
        if col not in df.columns:
            raise RuntimeError(f"Registry missing column: {col}")

    # Pick: extremes by size and class imbalance, plus a mid representative
    df = df.sort_values("train_patches")
    small = df.iloc[0]["dataset_id"]
    large = df.iloc[-1]["dataset_id"]

    df2 = df.sort_values("positive_pixel_rate")
    low_pos = df2.iloc[0]["dataset_id"]
    high_pos = df2.iloc[-1]["dataset_id"]

    picks = []
    for d in [small, large, low_pos, high_pos]:
        if d not in picks:
            picks.append(d)

    # If fewer than k, add highest-published-dice as additional
    if len(picks) < k:
        rest = df.sort_values("published_dice_sota", ascending=False)["dataset_id"].tolist()
        for d in rest:
            if d not in picks:
                picks.append(d)
            if len(picks) >= k:
                break

    return picks[:k]


def main():
    out_dir = Path("outputs") / "baselines"
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset_ids = pick_datasets("data/cell_benchmark_registry.json", k=4)

    cfg = TrainConfig()
    results = []
    for did in dataset_ids:
        print(f"\n=== Training baseline for {did} ===")
        res = train_one_dataset(did, cfg, out_dir)
        results.append(res)
        print(f"{did} val dice={res['val']['dice']:.4f} test dice={res['test']['dice']:.4f} epochs={res['epochs_ran']}")

    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump({"dataset_ids": dataset_ids, "cfg": cfg.__dict__, "results": results}, f, indent=2)


if __name__ == "__main__":
    main()
