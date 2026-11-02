import streamlit as st
import pandas as pd
import sqlite3

from database import create_database, extract_schema
from llm_generator import generate_sql
from sql_validator import validate_sql

# 1. Page configuration

st.set_page_config(
    page_title="AgentSQL",
    layout="wide"
)

st.title("AgentSQL")

st.subheader(
    "Schema-Guided Natural Language to SQL System"
)

st.write(
    "Ask questions in English and generate SQL "
    "using the Qwen2.5-Coder open-weight LLM."
)

st.divider()


# 2. Upload CSV dataset

st.header("1. Upload CSV Dataset")

uploaded_files = st.file_uploader(
    "Choose CSV files",
    type=["csv"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload a CSV dataset to continue.")
    st.stop()


# 3. Create SQLite database

try:

    conn = create_database(uploaded_files)

    schema = extract_schema(conn)

    st.success("Database created successfully!")

except Exception as error:

    st.error(f"Database error: {error}")
    st.stop()


# 4. Display database schema

st.header("2. Database Schema")

with st.expander("View tables and columns"):

    st.code(schema)


# 5. Enter natural language question
st.header("3. Ask Your Question")

question = st.text_area(
    "Enter your question",

    placeholder=(
        "Example: Find the customer who has "
        "the highest total spending."
    )
)


# 6. Generate SQL using the default prompt

if st.button("Generate SQL", type="primary"):

    if not question.strip():

        st.warning("Please enter a question.")

    else:

        # Clear previous result
        st.session_state.pop("result", None)

        try:

            with st.spinner(
                "Qwen is understanding your question "
                "and generating SQL..."
            ):

                result = generate_sql(
                    question,
                    schema
                )

            st.session_state.result = result
            st.session_state.question = question

        except Exception as error:

            st.error(
                f"LLM generation failed: {error}"
            )

# 7. Display generated SQL

if "result" in st.session_state:

    result = st.session_state.result

    st.header("4. LLM Output")

    if not result["answerable"]:

        st.warning(result["explanation"])

    else:

        sql = result["sql"]

        st.write("Generated SQL:")

        st.code(
            sql,
            language="sql"
        )

        st.write("Explanation:")

        st.write(result["explanation"])

        # 8. Validate SQL
        
        st.header("5. SQL Validation")

        valid, message = validate_sql(sql)

        if valid:

            st.success(message)


            # 9. Execute SQL safely
           
            if st.button("Execute SQL"):

                try:

                    # Enable read-only mode
                    conn.execute(
                        "PRAGMA query_only = ON"
                    )

                    # Allow only read-related SQLite operations
                    allowed_actions = {
                        sqlite3.SQLITE_SELECT,
                        sqlite3.SQLITE_READ,
                        sqlite3.SQLITE_FUNCTION,
                        getattr(
                            sqlite3,
                            "SQLITE_RECURSIVE",
                            -1
                        )
                    }

                    def authorizer(
                        action,
                        arg1,
                        arg2,
                        database,
                        trigger
                    ):

                        if action in allowed_actions:
                            return sqlite3.SQLITE_OK

                        return sqlite3.SQLITE_DENY


                    conn.set_authorizer(authorizer)

                    cursor = conn.cursor()

                    cursor.execute(sql)

                    if cursor.description is None:

                        raise ValueError(
                            "No result set returned."
                        )


                    columns = [
                        item[0]
                        for item in cursor.description
                    ]

                    rows = cursor.fetchmany(100)

                    df = pd.DataFrame(
                        rows,
                        columns=columns
                    )


                    # 10. Display query results

                    st.header("6. Query Results")

                    st.success(
                        "SQL executed successfully!"
                    )

                    st.dataframe(
                        df,
                        use_container_width=True
                    )

                    st.caption(
                        "Maximum 100 rows displayed."
                    )

                except Exception as error:

                    st.error(
                        f"Execution failed: {error}"
                    )

        else:

            st.error(message)


# 11. Footer

st.divider()

st.caption(
    "AgentSQL | Natural Language to SQL using Generative AI"
)
