import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    print("Connecting to MySQL server...")
    conn = pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'Somik12#')
    )
    cursor = conn.cursor()
    
    with open('database/schema.sql', 'r') as f:
        sql_script = f.read()
        
    # Split the script into individual statements
    statements = sql_script.split(';')
    
    for statement in statements:
        if statement.strip():
            print(f"Executing: {statement.strip()[:50]}...")
            cursor.execute(statement)
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Database setup complete!")

if __name__ == "__main__":
    setup_database()
