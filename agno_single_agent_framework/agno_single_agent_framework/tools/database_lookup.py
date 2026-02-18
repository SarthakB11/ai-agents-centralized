"""
Database Lookup Toolkit — Query PostgreSQL or MySQL databases using Agno framework.

Read-only SQL execution with safety checks.

Setup:
  pip install psycopg2-binary   # For PostgreSQL
  pip install pymysql            # For MySQL
  Set DATABASE_URL in .env (e.g., postgresql://user:pass@host/db)
"""

import os
import logging
from urllib.parse import urlparse
from agno.tools import Toolkit

logger = logging.getLogger(__name__)

# Blocked keywords to prevent destructive queries
BLOCKED_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]


class DatabaseLookupToolkit(Toolkit):
    """Toolkit for executing read-only SQL queries on databases."""

    def __init__(self, database_url: str = None):
        super().__init__(name="database_lookup")
        self._db_url = database_url or os.getenv("DATABASE_URL")
        self.register(self.query)
        self.register(self.list_tables)
        self.register(self.describe_table)

    def query(self, sql: str) -> dict:
        """
        Execute a read-only SQL SELECT query and return results.

        Only SELECT statements are allowed. INSERT, UPDATE, DELETE, DROP,
        and other write operations are blocked for safety.

        Args:
            sql: A read-only SQL SELECT query to execute

        Returns:
            A dictionary with rows, row_count, and column names
        """
        # Safety: Block write operations
        sql_upper = sql.strip().upper()
        for kw in BLOCKED_KEYWORDS:
            if kw in sql_upper:
                return {"error": f"Blocked: '{kw}' operations are not allowed. Read-only queries only."}

        if not self._db_url:
            return {"error": "DATABASE_URL not set in environment."}

        try:
            if "postgresql" in self._db_url or "postgres" in self._db_url:
                return self._query_postgres(sql)
            elif "mysql" in self._db_url:
                return self._query_mysql(sql)
            else:
                return {"error": f"Unsupported database type in URL."}
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {"error": str(e)}

    def list_tables(self) -> dict:
        """
        List all available tables in the database.

        Returns:
            A dictionary with a list of table names in the database
        """
        if not self._db_url:
            return {"error": "DATABASE_URL not set in environment."}

        if "postgresql" in self._db_url or "postgres" in self._db_url:
            sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        elif "mysql" in self._db_url:
            sql = "SHOW TABLES"
        else:
            return {"error": "Unsupported database type."}

        result = self.query(sql)
        if "error" in result:
            return result

        tables = [list(row.values())[0] for row in result.get("rows", [])]
        return {"tables": tables, "count": len(tables)}

    def describe_table(self, table_name: str) -> dict:
        """
        Get the column names and types for a specific database table.

        Args:
            table_name: The name of the table to describe

        Returns:
            A dictionary with column names and their data types
        """
        if not self._db_url:
            return {"error": "DATABASE_URL not set in environment."}

        if "postgresql" in self._db_url or "postgres" in self._db_url:
            sql = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}' AND table_schema = 'public'
                ORDER BY ordinal_position
            """
        elif "mysql" in self._db_url:
            sql = f"DESCRIBE {table_name}"
        else:
            return {"error": "Unsupported database type."}

        result = self.query(sql)
        if "error" in result:
            return result

        return {"table": table_name, "columns": result.get("rows", [])}

    def _query_postgres(self, sql: str) -> dict:
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            return {"error": "psycopg2 not installed. Run: pip install psycopg2-binary"}

        conn = psycopg2.connect(self._db_url)
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description] if cur.description else []
                return {"rows": [dict(r) for r in rows], "row_count": len(rows), "columns": columns}
        finally:
            conn.close()

    def _query_mysql(self, sql: str) -> dict:
        try:
            import pymysql
        except ImportError:
            return {"error": "pymysql not installed. Run: pip install pymysql"}

        parsed = urlparse(self._db_url)
        conn = pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip("/"),
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                return {
                    "rows": rows,
                    "row_count": len(rows),
                    "columns": list(rows[0].keys()) if rows else [],
                }
        finally:
            conn.close()


# Backward compatibility
DESCRIPTION = "Query a database with read-only SQL. Returns rows as list of dicts."
PARAMETERS = {
    "query": {"type": "string", "description": "Read-only SQL query (SELECT only)"},
    "database_url": {"type": "string", "description": "Override DB URL (optional)", "default": None},
}


def run(query: str, database_url: str = None) -> dict:
    """Execute a read-only SQL query (legacy interface)."""
    toolkit = DatabaseLookupToolkit(database_url=database_url)
    return toolkit.query(query)
