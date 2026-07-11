from app import app, db, User
from werkzeug.security import generate_password_hash
from sqlalchemy import text

from models import Role

def initialize_database(table_name, cs_col_name, title):
    
            db.session.execute(text(f"""
                CREATE VIRTUAL TABLE fts_{table_name} USING fts5(
                    {title},
                    tokenize = 'porter unicode61',
                    content={table_name},
                    content_rowid='id'
                )
            """))
                
            db.session.execute(text(f"""
                INSERT INTO fts_{table_name} (rowid{cs_col_name[cs_col_name.index(','):]})
                SELECT {cs_col_name} FROM {table_name}
            """))
            
            trigger_sql = [
                f"""
                CREATE TRIGGER {table_name}_ai AFTER INSERT ON {table_name}
                BEGIN
                    INSERT INTO fts_{table_name} (rowid{cs_col_name[cs_col_name.index(','):]})
                    VALUES ({",".join(["new."+ word for word in cs_col_name.split(',')])});
                END;
                """,
                f"""
                CREATE TRIGGER {table_name}_ad AFTER DELETE ON {table_name}
                BEGIN
                    INSERT INTO fts_{table_name} (fts_{table_name},rowid{cs_col_name[cs_col_name.index(','):]})
                    VALUES ('delete', {",".join(["old."+ word for word in cs_col_name.split(',')])});
                END;
                """,
                f"""
                CREATE TRIGGER {table_name}_au AFTER UPDATE ON {table_name}
                BEGIN
                    INSERT INTO fts_{table_name} (fts_{table_name},rowid{cs_col_name[cs_col_name.index(','):]})
                    VALUES ('delete', {",".join(["old."+ word for word in cs_col_name.split(',')])});
                    INSERT INTO fts_{table_name} (rowid{cs_col_name[cs_col_name.index(','):]})
                    VALUES ({",".join(["new."+ word for word in cs_col_name.split(',')])});
                END;
                """
            ]

            for sql in trigger_sql:
                db.session.execute(text(sql))
            
            db.session.commit()

def drop_fts_tables():
    fts_tables = ['fts_user', 'fts_company_profile', 'fts_student_profile', 'fts_placement_drive', 'fts_application', 'fts_placement_result']
    for table in fts_tables:
        try:
            db.session.execute(text(f"DROP TABLE IF EXISTS {table}"))
        except Exception as e:
            print(f"Error dropping table {table}: {e}")
    db.session.commit()

with app.app_context():
    drop_fts_tables()
    db.drop_all()
    db.create_all()
    initialize_database('user', 'id, username', 'username')
    initialize_database('company_profile', 'id, name', 'name')
    initialize_database('student_profile', 'id, name', 'name')
    initialize_database('placement_drive', 'id, title', 'title')
    initialize_database('application', 'id, date_applied', 'date_applied')
    initialize_database('placement_result', 'id, salary', 'salary')

    roles = ['Admin', 'Student', 'Company']
    for role_name in roles:
        entry = Role(
            name=role_name
        )
        db.session.add(entry)
        db.session.commit() 

    print("Database reset done!")