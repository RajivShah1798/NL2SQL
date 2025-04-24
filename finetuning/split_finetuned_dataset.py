import json
import random
from pathlib import Path

INPUT_FILE = "./preprocessed_data/spider/finetune_codet5_spider1.jsonl"
OUTPUT_DIR = "./preprocessed_data/spider/finetune_splits"
SPLIT_RATIO = (0.9, 0.05, 0.05) 
SEED = 42

def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]

def write_jsonl(path, data):
    with open(path, "w") as f:
        for row in data:
            f.write(json.dumps(row) + "\n")

def main():
    data = load_jsonl(INPUT_FILE)
    random.seed(SEED)
    random.shuffle(data)

    n = len(data)
    n_train = int(SPLIT_RATIO[0] * n)
    n_val = int(SPLIT_RATIO[1] * n)

    train_data = data[:n_train]
    val_data = data[n_train:n_train + n_val]
    test_data = data[n_train + n_val:]

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    write_jsonl(f"{OUTPUT_DIR}/train.jsonl", train_data)
    write_jsonl(f"{OUTPUT_DIR}/val.jsonl", val_data)
    write_jsonl(f"{OUTPUT_DIR}/test.jsonl", test_data)

    print(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

if __name__ == "__main__":
    main()
