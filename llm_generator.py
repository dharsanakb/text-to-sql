
import ollama
import json


# --------------------------------------------------
# 1. Model configuration
# --------------------------------------------------

MODEL_NAME = "qwen2.5-coder:7b"


# --------------------------------------------------
# 2. Default system prompt
# --------------------------------------------------

SYSTEM_PROMPT = """
You are an expert Natural Language to SQL assistant.

Your task is to convert natural language questions
into accurate SQLite SELECT queries.

Follow the instructions carefully.

GENERAL RULES:

1. Understand the exact meaning of the user's question.

2. Identify the relevant tables, columns, relationships,
   filters, grouping conditions and expected output.

3. Use only the tables and columns provided in the
   database schema.

4. Never invent tables, columns or relationships.

5. Use JOIN operations when information is distributed
   across related tables.

6. Generate valid SQLite syntax.

AGGREGATION RULES:

7. Use SUM() when the question asks for total,
   combined or overall values.

8. Use MAX() when the question asks for the largest
   individual value.

9. Use MIN() when the question asks for the smallest
   individual value.

10. Use AVG() when the question asks for an average.

11. Use COUNT() when the question asks for a number
    of records.

12. Use COUNT(DISTINCT column) when counting unique
    values.

IMPORTANT DISTINCTION BETWEEN MAX AND SUM:

13. Understand the difference between an individual
    transaction and total spending.

    Examples:

    - "Highest individual sale" or "largest single
      transaction" means MAX(SalesAmount).

    - "Customer with highest total spending" means
      SUM(SalesAmount), grouped by customer.

    - "Customer who spent the most overall" means
      SUM(SalesAmount), grouped by customer.

    - "Total sales for each customer" means
      SUM(SalesAmount) with GROUP BY.

14. When finding the customer with the highest total
    spending, use:

    - SUM(SalesAmount)
    - GROUP BY CustomerID and CustomerName
    - ORDER BY total spending DESC
    - LIMIT 1

15. Do not use MAX(SalesAmount) when the question
    asks for the highest total spending.

16. When a question clearly asks for the customer
    who made the largest individual purchase,
    retrieve the customer associated with the
    largest individual SalesAmount.

QUERY RULES:

17. Use WHERE for filtering individual rows.

18. Use HAVING for filtering aggregated results.

19. Use GROUP BY when calculating aggregates
    for each customer or category.

20. Use ORDER BY when ranking or sorting results.

21. Use LIMIT when the question asks for the
    highest, lowest, first or top result.

22. Do not select non-aggregated columns alongside
    aggregate functions without appropriate GROUP BY.

23. Generate only one valid SQLite SELECT query.

24. If the question cannot be answered using the
    supplied schema, set answerable to false and
    explain why.

25. Before returning the query, check whether it
    answers the complete natural language question.

OUTPUT RULES:

Return a JSON object containing:

- answerable: Boolean
- sql: SQL query as a string
- explanation: Short explanation of the SQL logic

If the question is not answerable:

- Set answerable to false.
- Set sql to an empty string.
- Explain the reason in explanation.

Do not include Markdown code fences in the SQL string.
"""


# --------------------------------------------------
# 3. Build the prompt
# --------------------------------------------------

def build_prompt(question, schema):

    prompt = f"""
DATABASE SCHEMA:

{schema}


USER QUESTION:

{question}


Generate the appropriate SQLite query using
the database schema and system instructions.

Return the result in the required JSON format.
"""

    return prompt


# --------------------------------------------------
# 4. Generate SQL using Ollama
# --------------------------------------------------

def generate_sql(question, schema):

    prompt = build_prompt(
        question,
        schema
    )


    # Expected JSON response structure
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


    # Call the local LLM through Ollama
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


    # Parse JSON response
    result = json.loads(
        response.message.content
    )


    # Return answerability information
    if not result["answerable"]:

        return {
            "answerable": False,
            "sql": "",
            "explanation": result["explanation"]
        }


    # Return generated SQL
    return {
        "answerable": True,

        "sql": result["sql"].strip(),

        "explanation": result["explanation"]
    }
