import psycopg2
import os

# Get environmental variable URL from Heroku
ENVIRONENT = os.environ.get("ENVIRONMENT")

if ENVIRONENT == "production":
    DATABASE = os.environ.get("DATABASE_URL")
elif ENVIRONENT == "test":
    DATABASE = os.environ.get("TEST_DATABASE_URL")

def db(command):

    # Establish connection with database
    db_conn = psycopg2.connect(DATABASE)

    # Create cursor to execute queries
    cursor = db_conn.cursor()

    # Creating a PostgreSQL table to store the data in
    if command == "create":

        create_summary_report_logs = """CREATE TABLE logs(
                     id SERIAL PRIMARY KEY,
                     summary BYTEA NOT NULL,
                     transcription BYTEA NOT NULL,
                     filename VARCHAR(255) NOT NULL,
                     summary_html BYTEA, 
                     link VARCHAR(255), 
                     time DATE NOT NULL, 
                     teacher VARCHAR(255), 
                     client_email VARCHAR(255),
                     client_name VARCHAR(255)
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
                    sidebar_comments BYTEA,
                    time DATE NOT NULL,
                    essay_grammar_mistakes BYTEA,
                    essay_linking_words BYTEA,
                    essay_repetitive_words BYTEA,
                    corrected_essay BYTEA
                    )"""

        #cursor.execute(create_summary_report_logs)
        #cursor.execute(create_essay_logs)
            
        db_conn.commit() # Commiting to make changes persistent 

        cursor.close()
        db_conn.close()
        print("DB created successfully!")

    elif command == "alter":
        #alter/update table

        #cursor.execute("""ALTER TABLE essay_logs ADD unnecessary_words_count BYTEA NOT NULL""")

        #cursor.execute("""ALTER TABLE Logs ADD client_email VARCHAR(255)""")
        #cursor.execute("""ALTER TABLE Logs ADD time DATE""")

        #cursor.execute("""ALTER TABLE essay_logs ADD essay_grammar_mistakes BYTEA""")
        #cursor.execute("""ALTER TABLE essay_logs ADD essay_linking_words BYTEA""")
        #cursor.execute("""ALTER TABLE essay_logs ADD essay_repetitive_words BYTEA""")
        #cursor.execute("""ALTER TABLE essay_logs ADD essay_unnecessary_words BYTEA""")
        #cursor.execute("""ALTER TABLE essay_logs ADD corrected_essay BYTEA""")

        cursor.execute("""ALTER SEQUENCE logs_id_seq RESTART WITH 10""")
        
        cursor.execute("""ALTER SEQUENCE essay_logs_id_seq RESTART WITH 5""")

        #cursor.execute("""ALTER SEQUENCE temp_storage_id_seq RESTART WITH 1""")

        #cursor.execute("""ALTER TABLE essay_logs RENAME COLUMN date TO time""")

        #cursor.execute("""ALTER TABLE essay_logs ALTER COLUMN sidebar_comments TYPE TEXT USING sidebar_comments::TEXT""")

        #cursor.execute("""UPDATE Logs SET id = 1 WHERE id = 2;""")

        #cursor.execute("""UPDATE Logs SET teacher = 'Carol' WHERE id = 2;""")

        #add_clients = """ 
        #UPDATE Logs SET client_email = 'drlamiaazizova@gmail.com' WHERE id = 1;
        #UPDATE Logs SET client_name = 'Lamia' WHERE id = 1;
        #"""

        #cursor.execute(add_clients)

        #cursor.execute("""UPDATE Logs SET link = 'https://www.dropbox.com/scl/fi/kkh4urusbik9mcvjcl1al/dr.shqazi-gmail.com_D_US_Carol_migraine_croup_Session1_16Nov24.mp4?rlkey=vqey0t1sgzmptrkhs4rs8h1yj&e=17&dl=0' WHERE id = 1;""")

        db_conn.commit()

        cursor.close()
        db_conn.close()

        return "Altered successfully!"
    
    elif command == "delete_data":

        cursor.execute(f"DELETE FROM Logs WHERE id IN ('8')") #'2', '3', '4', '5'
        cursor.execute(f"DELETE FROM essay_logs WHERE id IN ('5')")
        #cursor.execute(f"DELETE FROM temp_storage WHERE id IN ('1', '2', '3', '4')")

        db_conn.commit()

        cursor.close()
        db_conn.close()

        return "Data has been deleted from the database successfully!"

    elif command == "print":

        cursor.execute("SELECT * FROM Logs")
        #cursor.execute("SELECT * FROM essay_logs")
        #cursor.execute("SELECT * FROM temp_storage")

        rows = cursor.fetchall()

        for row in rows:
            print(row)

        cursor.close()
        db_conn.close()
    else:
        pass

def sent_email(id):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute(f"UPDATE Logs SET sent = 'True' WHERE id = {id}")
    #cursor.execute(f"UPDATE Logs SET sent = 'False' WHERE id = 1")

    db_conn.commit()

    cursor.close()
    db_conn.close()

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
        insert_sql = f"""INSERT INTO {db_name}(summary, transcription, filename, summary_html, link, time, teacher, client_email, client_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    elif db_name == "essay_logs":
        insert_sql = f"""INSERT INTO {db_name}(topic, essay, paragraphs_count, words_count, grammar_mistakes, linking_words_count, repetative_words_count, submitted_by, overall_band_score, sidebar_comments, time, essay_grammar_mistakes, essay_linking_words, essay_repetitive_words, corrected_essay) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    cursor.execute(insert_sql, data)

    db_conn.commit()

    cursor.close()
    db_conn.close()

    return "Data uploaded to the database successfully!"

def cache(data):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute("""SET datestyle = dmy;""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS temp_storage(
            id SERIAL PRIMARY KEY,
            link VARCHAR(255),
            time DATE,
            teacher_name VARCHAR(255),
            client_name VARCHAR(255),
            client_email VARCHAR(255)
        )
    """)

    cursor.execute("""
        INSERT INTO temp_storage(link, time, teacher_name, client_name, client_email) VALUES(%s, %s, %s, %s, %s);""", data)

    db_conn.commit()

def db_get_ids(table_name):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute(f"SELECT id FROM {table_name}")

    ids = cursor.fetchall()

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

        cursor.execute("SELECT summary, transcription, filename, summary_html, link, time, teacher, client_email, client_name, sent FROM Logs WHERE id = %s", (str(file_id)))

        file = cursor.fetchone()

        if file:

            summary = file[0]
            transcription = file[1]
            filename = file[2]
            summary_html = file[3]
            link = file[4]
            time = file[5]
            teacher = file[6]
            client_email = file[7]
            client_name = file[8]
            send = file[9]

            return [summary, transcription, filename, summary_html, link, time, teacher, client_email, client_name, send]
        
    elif db == "essay_logs":

        cursor.execute("SELECT topic, essay, paragraphs_count, words_count, grammar_mistakes, linking_words_count, repetative_words_count, submitted_by, overall_band_score, sidebar_comments, time, essay_grammar_mistakes, essay_linking_words, essay_repetitive_words, corrected_essay FROM essay_logs WHERE id = %s", (str(file_id)))

        file = cursor.fetchone()

        if file:

            lst = []
            for n in range(15):
                one = file[n]
                lst.append(one)

            return lst
    else:
        cursor.execute("SELECT link, time, teacher_name, client_name, client_email FROM temp_storage WHERE id = %s", str(file_id))

        file = cursor.fetchone()

        cursor.execute("DROP TABLE temp_storage")

        print("TABLE HAS BEEN DELETED")

        db_conn.commit()

        return file
    
    cursor.close()
    db_conn.close()

    return "File not found!", 404
