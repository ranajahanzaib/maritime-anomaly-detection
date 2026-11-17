from backend.app.db.session import engine, Base
import backend.app.models  # ensure models are registered


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
