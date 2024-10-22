import psycopg2
import os
import io

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
                    upload_time TIMESTAMP DEFAULT NOW()
                            )""")
            
        db_conn.commit() # Commiting to make changes persistent 

        cursor.close()
        db_conn.close()
        print("DB created successfully!")

    elif command == "update":
        #update table
        pass

    elif command == "delete":
        #delete table
        cursor.execute("""DROP DATABASE IF EXISTS Log""")
            
        db_conn.commit() # Commiting to make changes persistent 

        cursor.close()
        db_conn.close()
        print("DB deleted successfully!")

    else:
        pass


def delete_data_from_table(id):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute(f"DELETE FROM Logs WHERE id IS {id}")

    db_conn.commit()

    cursor.close()
    db_conn.close()

    return "Data has been deleted from the database successfully!"


def db_store(summary_report, transcription):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute(f"INSERT INTO Logs(summary, transcription) VALUES(%s, %s);", (summary_report, transcription))

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

    print(ids_lst)

    cursor.close()
    db_conn.close()

    return ids_lst


def db_retrieve(file_id):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute("SELECT summary, transcription FROM Logs WHERE id = %s", (str(file_id)))

    file = cursor.fetchone()

    if file:
        summary = file[0]
        transcription = file[1]
        #upload_time = file[2]

        file_obj_s = io.BytesIO(summary)
        file_obj_t = io.BytesIO(transcription)
        #file_obj_ut = io.BytesIO(upload_time)

        return [file_obj_s, file_obj_t]

    cursor.close()
    db_conn.close()

    return "File not found!", 404
