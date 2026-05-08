"""
Load data to PostgreSQL.

Bulk inserts data into the target table.
"""

import os


def load_to_postgres(data, table_name):
    """
    Insert data into PostgreSQL table.

    Args:
        data: List of dictionaries
        table_name: Target table name

    Returns:
        Number of rows inserted
    """

    import psycopg2

    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL", "")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Connect to database
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    try:
        rows_inserted = 0

        for row in data:
            # Skip empty rows
            if not row:
                continue

            # Build INSERT statement
            columns = list(row.keys())
            values = list(row.values())

            cols_str = ", ".join(columns)
            vals_str = ", ".join(["%s"] * len(values))
            query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str})"

            # Execute
            cur.execute(query, values)
            rows_inserted += 1

        # Commit transaction
        conn.commit()

        return rows_inserted

    finally:
        cur.close()
        conn.close()