import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-for-dev'
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'ai_marketplace'
    
    # Dummy SMTP for local dev
    SMTP_SERVER = os.environ.get('SMTP_SERVER') or 'localhost'
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or 1025)
    SMTP_USER = os.environ.get('SMTP_USER') or ''
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') or ''
