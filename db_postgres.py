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
                    transcription BYTEA NOT NULL.
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



def db_store(summary_report, transcription):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    #def create_file(text, name):
    #    with open(name, "wb") as file:
    #        file.write(text.encode('utf-8'))
    #    return file
    
    #summary_report_file = create_file(summary_report, "summary_report.odt")
    #transcription_file =  create_file(transcription, "transcription.odt")

    cursor.execute(f"INSERT INTO Logs(summary, transcription) VALUES(%s, %s);", (summary_report, transcription))
    #cursor.execute(f"INSERT INTO Log (summary_report, transcription) VALUES('transcription.odt', '{psycopg2.Binary(transcription)}');")

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

        file_obj_s = io.BytesIO(summary)
        file_obj_t = io.BytesIO(transcription)

        return [file_obj_s, file_obj_t]

    cursor.close()
    db_conn.close()

    return "File not found!", 404
