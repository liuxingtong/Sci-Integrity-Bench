"""Step 1: Reproducible preprocessing and scripted summaries."""

import pandas as pd
import json
import re
from collections import Counter
import os

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_PATH   = "data/interview_excerpts.csv"
OUT_DIR     = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} rows, columns: {list(df.columns)}")

# ── Basic cleaning ─────────────────────────────────────────────────────────
df["response_text"] = df["response_text"].str.strip()
df["word_count"]    = df["response_text"].apply(lambda t: len(t.split()))
df["char_count"]    = df["response_text"].apply(len)
df["sentence_count"]= df["response_text"].apply(
    lambda t: len(re.split(r'[.!?;]+', t.strip())))

# ── Cohort counts ──────────────────────────────────────────────────────────
cohort_counts = df["cohort"].value_counts().to_dict()
print("\nCohort counts:", cohort_counts)

# ── Length statistics by cohort ────────────────────────────────────────────
length_stats = df.groupby("cohort")[["word_count","char_count","sentence_count"]].agg(
    ["mean","median","std","min","max"]
).round(2)
print("\nLength stats by cohort:")
print(length_stats)

# ── Keyword / topic frequency ──────────────────────────────────────────────
# Define a priori topic keywords relevant to transit UX research
TOPIC_KEYWORDS = {
    "reliability":    ["reliable","reliability","delay","delays","on time","wrong","unreliable"],
    "information":    ["app","board","arrival","info","information","map","screen","interface","feed"],
    "safety":         ["safe","safety","unsafe","scary","lighting","cctv","alone","midnight"],
    "pricing":        ["price","pricing","cost","costs","fare","fares","fuel","discount","cap","caps"],
    "accessibility":  ["accessibility","accessible","elevator","outage","outages"],
    "crowding":       ["crowd","crowding","crowded","platform","skip"],
    "multimodal":     ["transfer","transfers","bike","park","parking","carpool","ride","driving","train","transit"],
    "trust":          ["trust","honest","reason","wrong","assume","erode"],
    "ux_design":      ["ux","interface","clutter","button","buttons","menu","menus","banner","banners","screen"],
}

def count_keywords(text, keywords):
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)

for topic, kws in TOPIC_KEYWORDS.items():
    df[f"topic_{topic}"] = df["response_text"].apply(lambda t: count_keywords(t, kws))

# Binary presence flag
for topic in TOPIC_KEYWORDS:
    df[f"flag_{topic}"] = (df[f"topic_{topic}"] > 0).astype(int)

# Topic mention rates by cohort
topic_flags = [f"flag_{t}" for t in TOPIC_KEYWORDS]
topic_rates = df.groupby("cohort")[topic_flags].mean().round(3)
print("\nTopic mention rates by cohort:")
print(topic_rates)

# ── Word frequency (top 30 per cohort) ────────────────────────────────────
STOPWORDS = set([
    "i","the","a","an","is","it","my","me","and","or","but","in","on","at",
    "to","of","for","with","that","this","when","if","not","are","be","so",
    "what","just","from","as","by","do","they","we","you","he","she","its",
    "than","more","even","only","would","will","can","have","has","was",
    "were","am","all","no","up","out","about","into","them","their","there",
    "which","who","how","some","any","same","two","three","one","know",
    "need","want","get","use","like","also","very","too","now","then",
    "those","these","over","after","before","because","through","never",
    "always","every","each","both","between","without","within","across",
    "around","near","next","last","first","second","new","old","good",
    "bad","big","small","long","short","right","left","own","other",
    "another","such","much","many","few","most","least","less","more",
    "where","while","since","until","though","although","however","still",
    "already","again","once","twice","often","sometimes","usually","never",
    "always","here","there","why","should","could","might","must","shall",
    "let","make","take","give","go","come","see","look","feel","think",
    "say","tell","ask","try","keep","put","set","run","work","show",
    "open","close","find","lose","miss","stop","start","end","turn",
    "move","leave","stay","help","call","send","read","write","play",
    "live","die","buy","sell","pay","spend","save","hold","bring","carry"
])

def top_words(texts, n=30):
    words = []
    for t in texts:
        tokens = re.findall(r"[a-z']+", t.lower())
        words.extend([w for w in tokens if w not in STOPWORDS and len(w) > 2])
    return Counter(words).most_common(n)

word_freq = {}
for cohort, grp in df.groupby("cohort"):
    word_freq[cohort] = top_words(grp["response_text"])
    print(f"\nTop words ({cohort}):")
    for w, c in word_freq[cohort][:15]:
        print(f"  {w}: {c}")

# ── Save processed data and summaries ─────────────────────────────────────
df.to_csv(f"{OUT_DIR}/processed_interviews.csv", index=False)

summary = {
    "cohort_counts": cohort_counts,
    "total_respondents": len(df),
    "length_stats": {
        cohort: {
            col: {
                stat: float(length_stats.loc[cohort, (col, stat)])
                for stat in ["mean","median","std","min","max"]
            }
            for col in ["word_count","char_count","sentence_count"]
        }
        for cohort in df["cohort"].unique()
    },
    "topic_mention_rates": {
        cohort: {
            t: float(topic_rates.loc[cohort, f"flag_{t}"])
            for t in TOPIC_KEYWORDS
        }
        for cohort in df["cohort"].unique()
    },
    "top_words": {
        cohort: word_freq[cohort]
        for cohort in word_freq
    }
}

with open(f"{OUT_DIR}/descriptive_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\n✓ Preprocessing complete. Files saved to outputs/")
