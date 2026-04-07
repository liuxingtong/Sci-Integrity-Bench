# Baseline scientist configs - run each in a SEPARATE terminal
# Working directory: ai_scientist project root (cd to project first)

# Terminal 1 - Scientist 0: 完全不知情，天使审稿人，深度审计概率固定 0.2
python meta_benchmark/meta_runner.py --scientist-config 0 --results-dir meta_runs --results-suffix baseline_s0

# Terminal 2 - Scientist 1: 成本信息 + 天使审稿人 + 深度审计概率固定 0.2
python meta_benchmark/meta_runner.py --scientist-config 1 --results-dir meta_runs --results-suffix baseline_s1

# Terminal 3 - Scientist 2: 成本信息 + 天使审稿人 + 深度审计概率动态
python meta_benchmark/meta_runner.py --scientist-config 2 --results-dir meta_runs --results-suffix baseline_s2

# Terminal 4 - Scientist 3: 成本信息 + permissive审稿人 + 深度审计概率固定 0
python meta_benchmark/meta_runner.py --scientist-config 3 --results-dir meta_runs --results-suffix baseline_s3
