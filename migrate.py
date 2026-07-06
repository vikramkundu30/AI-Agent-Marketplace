import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def migrate():
    conn = pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'Somik12#'),
        database=os.environ.get('MYSQL_DB', 'ai_marketplace')
    )
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN image_filename VARCHAR(255)")
        conn.commit()
        print("Migration successful: Added image_filename column.")
    except Exception as e:
        print(f"Migration error (might already exist): {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Create uploads directory if it doesn't exist
    os.makedirs('static/uploads', exist_ok=True)
    migrate()
