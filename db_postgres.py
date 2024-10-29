import psycopg2
import os
import io
from psycopg2.extensions import AsIs

# Get environmental variable URL from Heroku
DATABASE = os.environ.get("DATABASE_URL")

def db(command):

    # Establish connection with database
    db_conn = psycopg2.connect(DATABASE)

    # Create cursor to execute queries
    cursor = db_conn.cursor()

    # Creating a PostgreSQL table to store the data in
    if command == "create":
        cursor.execute("""CREATE TABLE Logs(
                    id SERIAL PRIMARY KEY,
                    summary BYTEA NOT NULL,
                    transcription BYTEA NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    upload_time TIMESTAMP DEFAULT NOW()
                            )""")
            
        db_conn.commit() # Commiting to make changes persistent 

        cursor.close()
        db_conn.close()
        print("DB created successfully!")

    elif command == "alter":
        #alter/update table

        #cursor.execute("""ALTER TABLE Logs ADD summary_html BYTEA""")

        #cursor.execute("""ALTER TABLE Logs ADD filename VARCHAR(255)""")

        cursor.execute("""ALTER SEQUENCE logs_id_seq RESTART WITH 4""")
        #"""SELECT setval('id', 2)"""

        db_conn.commit()

        cursor.close()
        db_conn.close()

        return "Altered successfully!"

    elif command == "delete_data":

        cursor.execute(f"DELETE FROM Logs WHERE id IN ('5', '34')")

        db_conn.commit()

        cursor.close()
        db_conn.close()

        return "Data has been deleted from the database successfully!"

    elif command == "delete_table":
        #delete table
        cursor.execute("""DROP DATABASE Logs""")
            
        db_conn.commit() # Commiting to make changes persistent 

        cursor.close()
        db_conn.close()
        print("DB deleted successfully!")

    elif command == "print":
        cursor.execute("SELECT * FROM Logs")

        rows = cursor.fetchall()

        for row in rows:
            print(row)

        cursor.close()
        db_conn.close()

    else:
        pass


def db_store(summary_report, transcription, filename, summary_html):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute(f"INSERT INTO Logs(summary, transcription, filename, summary_html) VALUES(%s, %s, %s, %s);", (summary_report, transcription, filename, summary_html))

    db_conn.commit()

    cursor.close()
    db_conn.close()

    return "File uploaded to the database successfully!"


def db_get_ids():

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute("SELECT id FROM Logs")

    ids = cursor.fetchall()
    
    ids_lst = []

    for id in ids:
        ids_lst.append(id[0])

    cursor.close()
    db_conn.close()

    return ids_lst


def db_retrieve(file_id):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute("SELECT summary, transcription, filename FROM Logs WHERE id = %s", (str(file_id)))

    file = cursor.fetchone()

    if file:
        summary = file[0]
        transcription = file[1]
        filename = file[2]

        return [summary, transcription, filename]

    cursor.close()
    db_conn.close()

    return "File not found!", 404
