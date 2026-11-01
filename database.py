# import os
# from pathlib import Path

# from dotenv import load_dotenv
# from sqlalchemy import create_engine
# from sqlalchemy.orm import declarative_base, sessionmaker

# load_dotenv()

# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "mysql+pymysql://root:password@localhost:3306/smartqueue",
# )
# if DATABASE_URL.startswith("mysql://"):
#     DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# connect_args = {}
# ca_path = os.getenv("MYSQL_SSL_CA")
# if ca_path and Path(ca_path).exists():
#     connect_args["ssl"] = {"ca": ca_path}

# engine = create_engine(
#     DATABASE_URL,
#     pool_pre_ping=True,
#     pool_recycle=3600,
#     connect_args=connect_args,
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(override=False)

db_user = os.getenv("DB_USER", "ad09b5_mediflow")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "mysql8010.site4now.net")
db_name = os.getenv("DB_NAME", "db_ad09b5_mediflow")
db_port = int(os.getenv("DB_PORT", "3306"))

if db_password:
    database_url = URL.create(
        drivername="mysql+pymysql",
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name,
    )
else:
    database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("Database configuration is missing")

connect_args = {}
ca_path = os.getenv("MYSQL_SSL_CA")

if ca_path and Path(ca_path).exists():
    connect_args["ssl"] = {"ca": ca_path}

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
