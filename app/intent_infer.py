from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import requests

MODEL_NAME = "microsoft/phi-1_5"

def _load_intent_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype="auto")

    llm = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        do_sample=False,
        temperature=0.0,
        max_new_tokens=300
    )
    return llm


def generate_intents(table_name, columns, data_types, llm=None):
    if not llm:
        llm = _load_intent_model(MODEL_NAME)
    few_shot_prompt = """
You're a helpful assistant. You are given the name of a SQL table and a list of columns with their types. 
Your task is to describe the likely purpose of this table in one sentence, and then describe what each listed column likely represents.

Only describe the columns listed. Do not add or describe any columns that are not explicitly given.

Example 1:
Table: inventory
Columns:
- item_id (INTEGER)
- item_name (TEXT)
- quantity (INTEGER)
- restock_date (DATE)

Table Purpose:
Tracks the stock levels and restocking schedules of items in a warehouse.

Column Descriptions:
- item_id: Unique identifier for each inventory item.
- item_name: Name or label of the item.
- quantity: Number of units currently in stock.
- restock_date: Date when the item is expected to be restocked.

---

Example 2:
Table: employee_attendance
Columns:
- employee_id (INTEGER)
- date (DATE)
- status (TEXT)

Table Purpose:
Logs the daily attendance status of company employees.

Column Descriptions:
- employee_id: Unique identifier for the employee.
- date: The calendar date of the attendance record.
- status: Attendance status for the day (e.g., Present, Absent, Sick).

---
""".strip()

    column_lines = "\n".join(
        [f"- {col} ({dtype})" for col, dtype in zip(columns, data_types)]
    )

    prompt = (
        f"{few_shot_prompt}\n\n"
        f"Table: {table_name}\n"
        f"Columns:\n{column_lines}\n\n"
        f"Table Purpose:\n"
    )

    result = llm(prompt, return_full_text=False)[0]["generated_text"]
    generated = result.strip()

    # Post-processing
    for stop_token in ["```", "2. Write a", "CREATE TABLE", "# Solution"]:
        if stop_token in generated:
            generated = generated.split(stop_token)[0].strip()

    table_intent = ""
    column_intents = {}

    expected_columns = set([col.lower() for col in columns])

    if "Column Descriptions:" in generated:
        table_intent, column_block = generated.split("Column Descriptions:", 1)
        table_intent = table_intent.strip()

        for line in column_block.strip().splitlines():
            if line.startswith("-") and ":" in line:
                try:
                    col, intent = line[1:].split(":", 1)
                    col = col.strip().lower()
                    if col in expected_columns:
                        column_intents[col] = intent.strip()
                except ValueError:
                    continue
    else:
        table_intent = generated

    return table_intent, column_intents


def call_generate_intents_api(api_url, table_name, columns, data_types):
    endpoint = f"{api_url}/generate_intents"
    headers = {"Content-Type": "application/json"}
    payload = {
        "table_name": table_name,
        "columns": columns,
        "data_types": data_types
    }

    response = requests.post(endpoint, json=payload, headers=headers)
    print("Response:\n", response.json())
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")
