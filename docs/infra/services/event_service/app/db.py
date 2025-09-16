from sqlmodel import SQLModel, create_engine, Session

# Use SQLite file (stored in same folder). You can change to PostgreSQL later.
DATABASE_URL = "sqlite:///./events.db"

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True will log SQL queries

# Create all tables if not already created
def init_db():
    from . import models  # import your Event model
    SQLModel.metadata.create_all(engine)

# Dependency for FastAPI routes
def get_session():
    with Session(engine) as session:
        yield session
