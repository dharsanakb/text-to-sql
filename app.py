
import streamlit as st
import pandas as pd
import sqlite3

from database import create_database, extract_schema
from llm_generator import generate_sql
from sql_validator import validate_sql


st.set_page_config(
    page_title="AgentSQL",
    layout="wide"
)

st.title("AgentSQL")
st.subheader("LLaMA-based Natural Language to SQL System")

st.write(
    "Ask questions in English and generate SQL "
    "using an open-weight LLaMA model."
)

st.divider()


# 1. Upload dataset

st.header("1. Upload CSV dataset")

uploaded_files = st.file_uploader(
    "Choose CSV files",
    type=["csv"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload a CSV dataset to continue.")
    st.stop()


# 2. Create database

try:

    conn = create_database(uploaded_files)
    schema = extract_schema(conn)

    st.success("Database created successfully!")

except Exception as error:

    st.error(f"Database error: {error}")
    st.stop()


# 3. Display schema

st.header("2. Database schema")

with st.expander("View tables and columns"):

    st.code(schema)


# 4. Enter natural language question

st.header("3. Ask your question")

question = st.text_area(
    "Enter your question",

    placeholder=(
        "Example: Show students who scored "
        "more than 80 marks."
    )
)


# 5. Select prompt strategy

strategy = st.selectbox(
    "Choose prompt engineering strategy",

    [
        "basic",
        "schema-aware",
        "few-shot"
    ],

    index=1
)


# 6. Generate SQL

if st.button("Generate SQL", type="primary"):

    if not question.strip():

        st.warning("Please enter a question.")

    else:

        try:

            with st.spinner(
                "LLaMA is understanding your question..."
            ):

                result = generate_sql(
                    question,
                    schema,
                    strategy
                )

            st.session_state.result = result
            st.session_state.question = question
            st.session_state.strategy = strategy

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

        st.code(sql, language="sql")

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

                    conn.execute(
                        "PRAGMA query_only = ON"
                    )

                    allowed_actions = {
                        sqlite3.SQLITE_SELECT,
                        sqlite3.SQLITE_READ,
                        sqlite3.SQLITE_FUNCTION,
                        sqlite3.SQLITE_RECURSIVE
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


st.divider()
