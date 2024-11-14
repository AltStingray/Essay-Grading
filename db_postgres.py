import psycopg2
import os
import io
from psycopg2.extensions import AsIs
from psycopg2.extras import Json, DictCursor

# Get environmental variable URL from Heroku
DATABASE = os.environ.get("DATABASE_URL")

def db(command):

    # Establish connection with database
    db_conn = psycopg2.connect(DATABASE)

    # Create cursor to execute queries
    cursor = db_conn.cursor()

    # Creating a PostgreSQL table to store the data in
    if command == "create":

        create_summary_report_logs = """CREATE TABLE Logs(
                     id SERIAL PRIMARY KEY,
                     summary BYTEA NOT NULL,
                     transcription BYTEA NOT NULL,
                     filename VARCHAR(255) NOT NULL,
                     upload_time TIMESTAMP DEFAULT NOW()
                             )"""

        create_essay_logs = """CREATE TABLE essay_logs(
                    id SERIAL PRIMARY KEY,
                    topic BYTEA NOT NULL,   
                    essay BYTEA NOT NULL,
                    paragraphs_count SMALLINT NOT NULL,
                    words_count SMALLINT NOT NULL,
                    grammar_mistakes SMALLINT NOT NULL,
                    linking_words_count SMALLINT NOT NULL,
                    repetative_words_count SMALLINT NOT NULL,
                    submitted_by BYTEA NOT NULL,
                    overall_band_score FLOAT NOT NULL,
                    sidebar_comments TEXT NOT NULL,
                    time DATE NOT NULL,
                    unnecessary_words_count SMALLINT NOT NULL)"""

        cursor.execute(create_essay_logs)
            
        db_conn.commit() # Commiting to make changes persistent 

        cursor.close()
        db_conn.close()
        print("DB created successfully!")

    elif command == "alter":
        #alter/update table

        #cursor.execute("""ALTER TABLE essay_logs ADD unnecessary_words_count BYTEA NOT NULL""")

        #cursor.execute("""ALTER TABLE Logs ADD filename VARCHAR(255)""")

        #cursor.execute("""ALTER SEQUENCE logs_id_seq RESTART WITH 6""")
        
        cursor.execute("""ALTER SEQUENCE essay_logs_id_seq RESTART WITH 1""")

        #cursor.execute("""ALTER TABLE essay_logs RENAME COLUMN date TO time""")

        #cursor.execute("""ALTER TABLE essay_logs ALTER COLUMN time TYPE DATE""")

        db_conn.commit()

        cursor.close()
        db_conn.close()

        return "Altered successfully!"

    elif command == "delete_data":

        #cursor.execute(f"DELETE FROM Logs WHERE id IN ('6')")
        cursor.execute(f"DELETE FROM essay_logs WHERE id IN ('1')")

        db_conn.commit()

        cursor.close()
        db_conn.close()

        return "Data has been deleted from the database successfully!"

    elif command == "print":
        cursor.execute("SELECT * FROM Logs")
        cursor.execute("SELECT * FROM essay_logs")

        rows = cursor.fetchall()

        for row in rows:
            print(row)

        cursor.close()
        db_conn.close()

    else:
        pass

def delete_table(table_name):
    db_conn = psycopg2.connect(DATABASE)

    db_conn.autocommit = True

    # Create cursor to execute queries
    cursor = db_conn.cursor()

    cursor.execute(f"DROP TABLE {table_name}")

    cursor.close()
    db_conn.close()

    return print("Table deleted successfully!")

def db_store(data, db_name):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    if db_name == "logs":
        insert_sql = f"""INSERT INTO {db_name}(summary, transcription, filename, summary_html) VALUES (%s, %s, %s, %s);"""
    else:
        insert_sql = f"""INSERT INTO {db_name}(topic, essay, paragraphs_count, words_count, grammar_mistakes, linking_words_count, repetative_words_count, submitted_by, overall_band_score, sidebar_comments, time, unnecessary_words_count) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    cursor.execute(insert_sql, data)

    db_conn.commit()

    cursor.close()
    db_conn.close()

    return "Data uploaded to the database successfully!"


def db_get_ids(table_name):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute(f"SELECT id FROM {table_name}")

    ids = cursor.fetchall()
    print(ids) # test
    ids_lst = []

    for id in ids:
        ids_lst.append(id[0])

    cursor.close()
    db_conn.close()

    return ids_lst


def db_retrieve(file_id, db):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    if db == "Logs":

        cursor.execute("SELECT summary, transcription, filename, summary_html FROM Logs WHERE id = %s", (str(file_id)))

        file = cursor.fetchone()

        if file:

            if file:
                summary = file[0]
                transcription = file[1]
                filename = file[2]
                summary_html = file[3]

            return [summary, transcription, filename, summary_html]
        
    elif db == "essay_logs":

        cursor.execute("SELECT topic, essay, paragraphs_count, words_count, grammar_mistakes, linking_words_count, repetative_words_count, submitted_by, overall_band_score, sidebar_comments, time, unnecessary_words_count FROM essay_logs WHERE id = %s", (str(file_id)))

        file = cursor.fetchone()

        if file:

            lst = []
            for n in range(12):
                one = file[n]
                lst.append(one)

            return lst

    cursor.close()
    db_conn.close()

    return "File not found!", 404
