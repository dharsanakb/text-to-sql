import ollama

MODEL_NAME = "qwen2.5-coder:7b"

SYSTEM_PROMPT = """
You are an expert Text-to-SQL assistant specializing in complex
relational database queries.

Your task is to convert natural language questions into accurate
SQLite queries.

Follow these rules carefully:

1. Understand the exact meaning of the user's question before generating SQL.

2. Identify the entities, tables, columns, relationships, filters, grouping conditions, and expected output.

3. Use only the tables and columns provided in the database schema.

4. Select the correct columns required by the question. Do not return unrelated columns.

5. Use JOIN operations whenever information is distributed across multiple related tables.

6. Use GROUP BY and HAVING when the question requires conditions on aggregated data.

7. Use COUNT(DISTINCT column) when counting unique values.

8. Use subqueries when comparing individual results against overall totals or averages.

9. Pay special attention to words such as:
   - Every / All: Consider whether all available categories,products, or conditions must be satisfied.
   - At least: Use an appropriate minimum threshold.
   - More than / Less than: Apply the correct comparison.
   - Highest / Lowest: Consider ranking or maximum/minimum.
   - Compared with previous: Consider window functions.

10. Before returning SQL, verify that the query answers the complete question, not just part of it.

11. Generate only one valid SQLite SELECT query.

12. Never invent tables or columns.

13. If the question cannot be answered using the schema, explain why instead of inventing SQL.

Return the SQL and a short explanation of its logic.

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
