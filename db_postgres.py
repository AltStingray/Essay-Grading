import psycopg2
import os

# Get environmental variable URL from Heroku
DATABASE = os.environ.get("DATABASE_URL")


def db(command):

    # Establish connection with database
    db_conn = psycopg2.connect(DATABASE)

    # Create cursor to execute queries
    cursor = db_conn.cursor()

    # Creating a PostgreSQL table to store the data in
    if command == "create":
        cursor.execute("""CREATE TABLE IF NOT EXISTS Log(
                    id serial primary key,
                    summary_report VARCHAR(10000) NOT NULL,
                    transcription VARCHAR(10000) NOT NULL
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
        pass

    else:
        pass



def db_store(summary_report, transcription):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    def create_file(text, name):
        with open(name, "w") as file:
            file.write(text)
        return file
    
    summary_report_file = create_file(summary_report, "summary_report.odt")
    transcription_file =  create_file(transcription, "transcription.odt")

    cursor.execute(f"INSERT INTO Log(summary_report, transcription) VALUES('{summary_report_file}', '{transcription_file}');")

    db_conn.commit()

    cursor.close()
    db_conn.close()


def db_retrieve():

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    #SELECT * FROM Log WHERE id = {id}
    cursor.execute(f'SELECT * FROM Log;')

    print(cursor.fetchall())
    logs = cursor.fetchall()

    db_conn.commit()

    cursor.close()
    db_conn.close()

    return logs
