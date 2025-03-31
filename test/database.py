import psycopg2 as psql
from psycopg2.extensions import connection

def connect(database) -> connection:
    conn = psql.connect(
        dbname=database["Name"],
        user=database["User"],
        password=database["Password"],
        host=database["Host"],
        port=database["Port"]
    )
    return conn

def create_metrics_table(conn: connection) -> None:
    # Create a cursor
    cur = conn.cursor()
    
    # Create the table
    cur.execute(f"""
                CREATE TABLE IF NOT EXISTS metrics (
                    id serial PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    server_id INT NOT NULL,
                    cpu_usage FLOAT NOT NULL,
                    memory_available FLOAT NOT NULL,
                    memory_used FLOAT NOT NULL,
                    disk_available FLOAT NOT NULL,
                    disk_used FLOAT NOT NULL
                );
                """)
    
    # Commit the transaction
    conn.commit()
    
    # Close the cursor
    cur.close()

def create_endpoints_table(conn: connection) -> None:
    # Create a cursor
    cur = conn.cursor()
    
    # Create the table
    cur.execute(f"""
                CREATE TABLE IF NOT EXISTS endpoints (
                    id serial PRIMARY KEY,
                    endpoint VARCHAR(255) NOT NULL,
                    status BOOLEAN NOT NULL DEFAULT TRUE
                );
                """)
    
    # Commit the transaction
    conn.commit()
    
    # Close the cursor
    cur.close()

def insert_metrics_data(conn: connection, data: list) -> None:
    # Create a cursor
    cur = conn.cursor()
    
    # Insert the data
    cur.executemany(
        f"""
        INSERT INTO metrics (server_id, cpu_usage, memory_available, memory_used, disk_available, disk_used)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        data
        )
    
    # Commit the transaction
    conn.commit()
    
    # Close the cursor
    cur.close()

def insert_endpoints_data(conn: connection, data: list) -> None:
    # Create a cursor
    cur = conn.cursor()
    
    # Insert the data
    cur.executemany(
        f"""
        UPDATE endpoints
        SET status = %s
        WHERE id = %s;
        """,
        data
        )
    
    # Commit the transaction
    conn.commit()
    
    # Close the cursor
    cur.close()

def update_endpoints_data(conn: connection, data: list) -> None:
    # Create a cursor
    cur = conn.cursor()
    
    # Insert the data
    cur.executemany(
        f"""
        UPDA
        """,
        data
        )
    
    # Commit the transaction
    conn.commit()
    
    # Close the cursor
    cur.close()
    
def insert_data(table: str, data: list) -> int:
    conn = connect()
    cur = conn.cursor()
    
    cur.executemany(
        f"""
        INSERT INTO {table} (host_name, host_password)
        VALUES (%s, %s);
        """,
        data
        )
    
    conn.commit()
    cur.close()
    conn.close()
    return 1

def query_data(query: str) -> list:
    conn = connect()
    cur = conn.cursor()
    
    cur.execute(query)
    
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data