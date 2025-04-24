import json
from tqdm import tqdm
from collections import defaultdict

SPIDER_QUESTIONS = "./raw_data/spider/train_spider.json"
ENRICHED_TABLES = "./preprocessed_data/spider/spider_with_intents.json"
OUTPUT_FILE = "./preprocessed_data/spider/finetune_codet5_spider1.jsonl"

def load_json(path):
    with open(path) as f:
        return json.load(f)

def build_prompt(example, db_schema, include_sql=True):
    lines = []
    lines.append(f"### Database: {example['db_id']}")
    lines.append("")


    for table in db_schema:
        lines.append(f"### Table Schema: {table['table_name']} - {table['table_intent']}")
        for col in table["columns"]:
            col_name, col_type = col.split(" (", 1)
            col_type = col_type.rstrip(")")
            col_intent = table["column_intents"].get(col_name.lower(), "")
            lines.append(f"- {col_name} ({col_type}): {col_intent}")
        lines.append("")

    lines.append(f"### Question: {example['question']}")
    if include_sql:
        lines.append("### SQL:")

    return "\n".join(lines)

def main():
    questions = load_json(SPIDER_QUESTIONS)
    enriched_tables = load_json(ENRICHED_TABLES)

    db_schema_map = defaultdict(list)
    for entry in enriched_tables:
        db_schema_map[entry["db_id"]].append(entry)

    output_data = []

    for ex in tqdm(questions):
        db_id = ex["db_id"]
        if db_id not in db_schema_map:
            continue

        schema_info = db_schema_map[db_id]
        prompt = build_prompt(ex, schema_info)
        completion = ex["query"]

        output_data.append({
            "db_id": db_id,
            "prompt": prompt,
            "completion": completion
        })

    with open(OUTPUT_FILE, "w") as f:
        for row in output_data:
            f.write(json.dumps(row) + "\n")

    print(f"\nSaved training data to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
