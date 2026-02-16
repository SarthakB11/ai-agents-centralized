"""
Database Lookup Tool — Query PostgreSQL or MySQL databases.

Setup:
  pip install psycopg2-binary   # For PostgreSQL
  pip install pymysql            # For MySQL
  Set DATABASE_URL in .env (e.g., postgresql://user:pass@host/db)
"""

import os
import logging

logger = logging.getLogger(__name__)

DESCRIPTION = "Query a database with read-only SQL. Returns rows as list of dicts."

PARAMETERS = {
    "query": {"type": "string", "description": "Read-only SQL query (SELECT only)"},
    "database_url": {"type": "string", "description": "Override DB URL (optional)", "default": None},
}

# Blocked keywords to prevent destructive queries
BLOCKED_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]


def run(query: str, database_url: str = None) -> dict:
    """Execute a read-only SQL query and return results."""

    # Safety: Block write operations
    query_upper = query.strip().upper()
    for kw in BLOCKED_KEYWORDS:
        if kw in query_upper:
            return {"error": f"Blocked: '{kw}' operations are not allowed. Read-only queries only."}

    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        return {"error": "DATABASE_URL not set in environment."}

    try:
        if "postgresql" in db_url or "postgres" in db_url:
            return _query_postgres(query, db_url)
        elif "mysql" in db_url:
            return _query_mysql(query, db_url)
        else:
            return {"error": f"Unsupported database type in URL: {db_url[:20]}..."}
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {"error": str(e)}


def _query_postgres(query: str, db_url: str) -> dict:
    """Execute query on PostgreSQL."""
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        return {"error": "psycopg2 not installed. Run: pip install psycopg2-binary"}

    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return {
                "rows": [dict(r) for r in rows],
                "row_count": len(rows),
                "columns": columns,
            }
    finally:
        conn.close()


def _query_mysql(query: str, db_url: str) -> dict:
    """Execute query on MySQL."""
    try:
        import pymysql
    except ImportError:
        return {"error": "pymysql not installed. Run: pip install pymysql"}

    # Parse connection from URL: mysql://user:pass@host:port/db
    from urllib.parse import urlparse
    parsed = urlparse(db_url)

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
            cur.execute(query)
            rows = cur.fetchall()
            return {
                "rows": rows,
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if rows else [],
            }
    finally:
        conn.close()
