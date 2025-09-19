import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import with absolute imports
try:
    from database import DATABASE_URL, Base
    from models import User, Machine, ApiKey
except ImportError:
    # Try relative imports if absolute fails
    from .database import DATABASE_URL, Base
    from .models import User, Machine, ApiKey

# Load environment variables
load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Parse DATABASE_URL to get connection details
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "control")
        db_user = os.getenv("DB_USER", "control")
        db_password = os.getenv("DB_PASSWORD", "controlpass")

        # Connect to MySQL server (without specifying database)
        server_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}"
        server_engine = create_engine(server_url)

        with server_engine.connect() as conn:
            # Create database if it doesn't exist
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
            conn.commit()
            print(f"Database '{db_name}' created or already exists")

    except Exception as e:
        print(f"Error creating database: {e}")
        raise


def run_migrations():
    """Create all tables and run SQL migrations"""
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")

        # Run SQL migrations
        run_sql_migrations(engine)

        return engine
    except Exception as e:
        print(f"Error running migrations: {e}")
        raise


def run_sql_migrations(engine):
    """Execute SQL migration files from migrations directory"""
    try:
        migrations_dir = os.path.join(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))), 'migrations')

        if not os.path.exists(migrations_dir):
            print("No migrations directory found, skipping SQL migrations")
            return

        # Get all .sql files and sort them
        sql_files = [f for f in os.listdir(
            migrations_dir) if f.endswith('.sql')]
        sql_files.sort()

        if not sql_files:
            print("No SQL migration files found")
            return

        print(f"Found {len(sql_files)} migration files")

        # Create migrations tracking table if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL UNIQUE,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

            # Check which migrations have already been executed
            result = conn.execute(
                text("SELECT filename FROM migration_history"))
            executed_migrations = {row[0] for row in result}

            # Execute new migrations
            for sql_file in sql_files:
                if sql_file in executed_migrations:
                    print(f"Migration {sql_file} already executed, skipping")
                    continue

                print(f"Executing migration: {sql_file}")

                # Read and execute the SQL file
                file_path = os.path.join(migrations_dir, sql_file)
                with open(file_path, 'r') as f:
                    sql_content = f.read()

                # Split by semicolon and execute each statement
                statements = [stmt.strip()
                              for stmt in sql_content.split(';') if stmt.strip()]

                try:
                    for statement in statements:
                        if statement and not statement.startswith('--'):
                            conn.execute(text(statement))

                    # Record successful migration
                    conn.execute(text(
                        "INSERT INTO migration_history (filename) VALUES (:filename)"
                    ), {"filename": sql_file})

                    conn.commit()
                    print(f"Migration {sql_file} executed successfully")

                except Exception as e:
                    conn.rollback()
                    print(f"Error executing migration {sql_file}: {e}")
                    raise

        print("All migrations completed successfully")

    except Exception as e:
        print(f"Error running SQL migrations: {e}")
        raise


def seed_superadmin(engine):
    """Create superadmin user if it doesn't exist"""
    try:
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Check if superadmin already exists
        existing_admin = db.query(User).filter(
            User.username == "admin").first()

        if not existing_admin:
            # Create superadmin user
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            hashed_password = hash_password(admin_password)

            superadmin = User(
                username="admin",
                hashed_password=hashed_password,
                is_active=True
            )

            db.add(superadmin)
            db.commit()
            print(f"Superadmin user created with username: admin")
            print(f"Default password: {admin_password}")
            print("Please change the default password after first login!")
        else:
            print("Superadmin user already exists")

        db.close()

    except Exception as e:
        print(f"Error seeding superadmin: {e}")
        raise


def seed_sample_data(engine):
    """Seed sample data for development"""
    try:
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Check if sample data already exists
        existing_machines = db.query(Machine).count()

        if existing_machines == 0:
            # Create sample machines with specific data
            sample_machines = [
                Machine(
                    name="Macbook Pro M2",
                    hostname="scismic.local",
                    ip_address="192.168.100.72",
                    mac_address="f6:88:5f:f9:87:69",
                    ha_entity_id=None,
                    description=None,
                    is_active=True
                ),
                Machine(
                    name="3900x",
                    hostname="JP",
                    ip_address="192.168.100.10",
                    mac_address="50-E0-85-8B-4E-4E",
                    ha_entity_id=None,
                    description=None,
                    is_active=True
                )
            ]

            for machine in sample_machines:
                db.add(machine)

            db.commit()
            print("Sample machines created with specific data")
        else:
            print("Sample data already exists")

        db.close()

    except Exception as e:
        print(f"Error seeding sample data: {e}")
        # Don't raise here as sample data is optional
        pass


def main():
    """Main initialization function"""
    print("Starting database initialization...")

    try:
        # Step 1: Create database if it doesn't exist
        create_database_if_not_exists()

        # Step 2: Run migrations (create tables)
        engine = run_migrations()

        # Step 3: Seed superadmin user
        seed_superadmin(engine)

        # Step 4: Seed sample data (optional)
        if os.getenv("SEED_SAMPLE_DATA", "false").lower() == "true":
            seed_sample_data(engine)

        print("Database initialization completed successfully!")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
