from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError

# localhost
# URL_DATABASE = 'postgresql://postgres:1234@localhost:5432/ReadSpeakDB'
# supabase
URL_DATABASE = 'postgresql://postgres.zzcbfheemrrkfoflzblg:Klxoht0BqqQCdYX7@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'
# render
# URL_DATABASE = 'postgresql://read_user:Su3ESCItyqSKI5wuEvuzjOMAtVHBmH5W@dpg-cv95oql2ng1s73d0d63g-a.singapore-postgres.render.com/read'

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()

# try:
#     engine = create_engine(URL_DATABASE)
#     engine.connect()  # Attempt to connect
#     print("Database connection successful!")

#     #Optional: Check if tables exist.
#     #from sqlalchemy import inspect
#     #inspector = inspect(engine)
#     #print(inspector.get_table_names())

# except OperationalError as e:
#     print(f"Database connection failed: {e}")
# except Exception as e:
#     print(f"An unexpected error occurred: {e}")