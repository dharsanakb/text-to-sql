
import sqlglot
from sqlglot import exp


def validate_sql(sql):

    if not sql or not sql.strip():
        return False, "SQL query is empty."

    try:

        statements = sqlglot.parse(
            sql,
            read="sqlite"
        )

        statements = [
            s for s in statements
            if s is not None
        ]

        if len(statements) != 1:
            return False, "Only one SQL statement is allowed."

        tree = statements[0]

        allowed = (
            exp.Select,
            exp.Union,
            exp.Intersect,
            exp.Except
        )

        if not isinstance(tree, allowed):
            return False, "Only SELECT queries are allowed."

        forbidden = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Create,
            exp.Alter,
            exp.Command
        )

        for operation in forbidden:

            if tree.find(operation):
                return False, "Unsafe SQL operation detected."

        return True, "SQL syntax and operation check passed."

    except Exception as error:

        return False, f"Invalid SQL: {error}"
