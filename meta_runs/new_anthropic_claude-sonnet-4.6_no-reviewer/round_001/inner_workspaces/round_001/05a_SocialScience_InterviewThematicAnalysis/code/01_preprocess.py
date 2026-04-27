"""Step 1: Reproducible preprocessing and scripted summaries."""

import csv
import json
import re
from collections import Counter
import os

DATA_PATH = "data/interview_excerpts.csv"
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

rows = []
with open(DATA_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print(f"Total respondents: {len(rows)}")

cohort_counts = Counter(r["cohort"] for r in rows)
print("\nCohort counts:")
for cohort, n in sorted(cohort_counts.items()):
    print(f"  {cohort}: {n}")

for r in rows:
    text = r["response_text"]
    r["char_len"] = len(text)
    r["word_count"] = len(text.split())

for cohort in sorted(cohort_counts):
    subset = [r for r in rows if r["cohort"] == cohort]
    avg_chars = sum(r["char_len"] for r in subset) / len(subset)
    avg_words = sum(r["word_count"] for r in subset) / len(subset)
    print(f"\n{cohort}:")
    print(f"  avg char length : {avg_chars:.1f}")
    print(f"  avg word count  : {avg_words:.1f}")
    print(f"  min words       : {min(r['word_count'] for r in subset)}")
    print(f"  max words       : {max(r['word_count'] for r in subset)}")

STOPWORDS = {
    "i","the","a","an","is","it","in","on","at","to","and","or","but",
    "not","for","of","my","me","that","this","when","if","are","be",
    "with","from","what","so","as","by","do","its","they","them","their",
    "we","he","she","was","were","have","has","had","would","will","can",
    "just","than","more","only","even","like","know","get","use","need",
    "want","am","up","out","no","one","two","three","all","some","any",
    "which","who","how","why","where","there","here","then","now","also",
    "about","into","over","after","before","because","through","same",
    "those","these","such","both","each","other","own","very","too",
    "could","should","may","might","must","shall","does","did","been",
    "being","make","made","take","taken","give","given","go","going",
    "come","coming","see","seen","say","said","tell","told","think",
    "thought","feel","felt","let","put","set","keep","kept","show",
    "shown","find","found","seem","seemed","look","looked","turn",
    "turned","leave","left","call","called","try","tried","ask","asked",
    "work","worked","move","moved","live","lived","play","played",
    "run","ran","hold","held","bring","brought","write","wrote",
    "stand","stood","hear","heard","mean","meant","read",
    "spend","spent","grow","grew","open","opened","close","closed",
    "follow","followed","stop","stopped","start","started","end","ended",
    "help","helped","change","changed","include","included","continue",
    "continued","become","became","begin","began","allow","allowed",
    "add","added","create","created","build","built","provide","provided",
    "consider","considered","appear","appeared","buy","bought","wait",
    "waited","serve","served","send","sent","expect",
    "expected","stay","stayed","fall","fell","cut","reach",
    "reached","remain","remained","suggest","suggested",
    "raise","raised","pass","passed","sell","sold","require","required",
    "report","reported","decide","decided","pull","pulled","break",
    "broke","win","won","pay","paid","meet","met",
    "set","learn","learned","cover","covered","drive","drove",
    "carry","carried","throw","threw","choose","chose","fight","fought",
    "draw","drew","wear","wore","catch","caught","eat","ate","sleep",
    "slept","sit","sat","fly","flew","ride","rode",
    "sing","sang","ring","rang","drink","drank",
    "blow","blew","forget","forgot","freeze",
    "froze","hide","hid","hit","hurt","lay","laid",
    "lead","led","lend","lent","lose","lost",
    "overcome","overcame","prove","proved","quit","rise","rose",
    "shake","shook","shine","shone","shoot","shot","shrink","shrank",
    "shut","sink","sank","slide","slid","spread",
    "spring","sprang","steal","stole","stick","stuck","sting","stung",
    "strike","struck","swear","swore","sweep","swept","swing","swung",
    "teach","taught","tear","tore","understand","understood","upset",
    "wake","woke","weep","wept","withdraw","withdrew",
    "first","second","third","fourth","fifth",
    "last","next","previous","current","new","old","good","bad",
    "big","small","large","little","long","short","high","low",
    "right","wrong","true","false","real","fake","free","full",
    "half","whole","part","many","much","few","several",
    "enough","another","every","either","neither","none","nothing",
    "everything","something","anything","someone","anyone","everyone",
    "nobody","everybody","somebody","anybody","nowhere","everywhere",
    "somewhere","anywhere","somehow","anyhow","anyway",
    "however","whatever","whenever","wherever","whoever","whichever",
    "whomever","whatsoever",
    "also","therefore","thus","hence","moreover","furthermore",
    "nevertheless","nonetheless","meanwhile","otherwise",
    "instead","rather","besides","indeed","certainly","probably",
    "possibly","perhaps","maybe","actually","really","quite",
    "fairly","pretty","somewhat","slightly","nearly","almost","already",
    "still","yet","soon","today","yesterday","tomorrow","always",
    "never","often","usually","sometimes","rarely","seldom","ever",
    "once","twice","again","together","apart","away","back","down",
    "forward","home","inside","outside","around","across","along",
    "behind","beside","beyond","near","opposite","past",
    "toward","towards","within","without","upon","onto","amid",
    "among","amongst","despite","except","per","plus","versus",
    "via","vs","etc",
}

def tokenize(text):
    tokens = re.findall(r"[a-z']+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

all_tokens = []
for r in rows:
    all_tokens.extend(tokenize(r["response_text"]))
overall_freq = Counter(all_tokens)
print("\nTop 20 words (all respondents):")
for word, cnt in overall_freq.most_common(20):
    print(f"  {word}: {cnt}")

cohort_freq = {}
for cohort in sorted(cohort_counts):
    tokens = []
    for r in rows:
        if r["cohort"] == cohort:
            tokens.extend(tokenize(r["response_text"]))
    cohort_freq[cohort] = Counter(tokens)
    print(f"\nTop 15 words ({cohort}):")
    for word, cnt in cohort_freq[cohort].most_common(15):
        print(f"  {word}: {cnt}")

summary = {
    "total_respondents": len(rows),
    "cohort_counts": dict(cohort_counts),
    "respondents": [
        {
            "respondent_id": r["respondent_id"],
            "cohort": r["cohort"],
            "char_len": r["char_len"],
            "word_count": r["word_count"],
            "response_text": r["response_text"],
        }
        for r in rows
    ],
    "overall_top20": overall_freq.most_common(20),
    "cohort_top15": {
        cohort: cohort_freq[cohort].most_common(15)
        for cohort in cohort_freq
    },
}

with open(f"{OUT_DIR}/preprocessing_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(f"\nSaved: {OUT_DIR}/preprocessing_summary.json")
