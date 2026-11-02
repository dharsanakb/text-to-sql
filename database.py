import sqlite3
import pandas as pd
import re
import json


def clean_table_name(filename):
    name = filename.rsplit(".", 1)[0].lower()
    name = re.sub(r"\W+", "_", name).strip("_")

    if not name:
        name = "uploaded_table"

    if name[0].isdigit():
        name = "table_" + name

    return name


def create_database(uploaded_files):
    conn = sqlite3.connect(":memory:")
    used_names = set()

    for file in uploaded_files:
        table_name = clean_table_name(file.name)
        original_name = table_name
        counter = 1

        while table_name in used_names:
            table_name = f"{original_name}_{counter}"
            counter += 1

        df = pd.read_csv(file)
        df.columns = df.columns.astype(str).str.strip()

        if df.empty or len(df.columns) == 0:
            continue

        if not all(col for col in df.columns):
            raise ValueError("Invalid or empty column names.")

        if not df.columns.is_unique:
            raise ValueError("Duplicate column names found.")

        df.to_sql(
            table_name,
            conn,
            index=False,
            if_exists="replace"
        )

        used_names.add(table_name)

    if not used_names:
        conn.close()
        raise ValueError("No valid CSV data found.")

    return conn


def extract_schema(conn):
    cursor = conn.cursor()

    tables = cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """).fetchall()

    schema = ""

    for (table_name,) in tables:
        columns = cursor.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()

        schema += f"\nTable: {table_name}\n"
        schema += "Columns:\n"

        for column in columns:
            schema += f"- {column[1]} ({column[2]})\n"

    return schema


def schema_to_json(schema):
    return json.dumps(schema, indent=4)