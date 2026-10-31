import ollama

MODEL_NAME = "llama3.1:8b"

SYSTEM_PROMPT = """
You are QueryPilot, an expert Text-to-SQL generator.

Your task is to convert natural language questions
into valid SQLite SQL queries.

Follow these rules:

1. Use only tables and columns supplied in the schema.
2. Never invent table or column names.
3. Understand the user's intended operation.
4. Generate valid SQLite SQL syntax.
5. Generate only one SQL statement.
6. Generate read-only SELECT queries only.
7. Never generate INSERT, UPDATE, DELETE,
   DROP, ALTER or CREATE statements.
8. If the question cannot be answered using
   the schema, set answerable to false.
9. Return a JSON response matching the
   requested output format.
"""


def build_prompt(question, schema, strategy):

    if strategy == "basic":

        prompt = f"""
Convert the following natural language
question into a SQLite SQL query.

Question:
{question}

Return the SQL query in JSON format.
"""

    elif strategy == "schema-aware":

        prompt = f"""
DATABASE SCHEMA:

{schema}

USER QUESTION:

{question}

Instructions:

1. Identify the relevant table.
2. Identify the required columns.
3. Identify conditions and filters.
4. Identify aggregation or grouping if needed.
5. Generate the corresponding SQLite query.

Use only the supplied schema.
"""

    elif strategy == "few-shot":

        prompt = f"""
DATABASE SCHEMA:

{schema}

EXAMPLES:

Question: Show all students.

SQL:
SELECT * FROM students;

Question: Count all students.

SQL:
SELECT COUNT(*) FROM students;

Question: Show students scoring above 80.

SQL:
SELECT * FROM students
WHERE marks > 80;

Question: Find the average marks.

SQL:
SELECT AVG(marks) FROM students;

NOW GENERATE SQL FOR:

{question}

Use only tables and columns
from the provided database schema.
"""

    else:

        raise ValueError("Unknown prompt strategy.")


    return prompt


def generate_sql(question, schema, strategy="schema-aware"):

    prompt = build_prompt(
        question,
        schema,
        strategy
    )

    response_schema = {
        "type": "object",
        "properties": {
            "answerable": {
                "type": "boolean"
            },
            "sql": {
                "type": "string"
            },
            "explanation": {
                "type": "string"
            }
        },
        "required": [
            "answerable",
            "sql",
            "explanation"
        ]
    }

    response = ollama.chat(
        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        format=response_schema,

        options={
            "temperature": 0
        },

        stream=False
    )

    import json

    result = json.loads(
        response.message.content
    )

    if not result["answerable"]:
        return {
            "answerable": False,
            "sql": "",
            "explanation": result["explanation"]
        }

    return {
        "answerable": True,
        "sql": result["sql"].strip(),
        "explanation": result["explanation"]
    }
