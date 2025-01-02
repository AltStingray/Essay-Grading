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

def db_store(data, db_name):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()
    
    if db_name == "logs":
        insert_sql = f"""INSERT INTO {db_name}(summary, transcription, filename, summary_html, link, time, teacher, client_email, client_name, precise_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
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

    cursor.close()
    db_conn.close()

def del_cache():

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute("DROP TABLE temp_storage")

    print("TABLE HAS BEEN DELETED")

    db_conn.commit()

def table_exists(table_name):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute("""SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)""", (table_name,))

    table_exists = cursor.fetchone()[0]

    return table_exists


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

def save_change(html, id):
    '''Saving changes in selected summary report'''

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    cursor.execute("UPDATE TABLE Logs set summary_html = %s WHERE id = %s;", html, id)

    cursor.close()
    db_conn.close()

    return "Change have been saved successfully!", 200

def db_retrieve(file_id, db):

    db_conn = psycopg2.connect(DATABASE)

    cursor = db_conn.cursor()

    if db == "Logs":

        cursor.execute("SELECT summary, transcription, filename, summary_html, link, time, teacher, client_email, client_name, sent, precise_time, sent_array FROM Logs WHERE id = %s", (str(file_id),))

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
            sent = file[9]
            precise_time = file[10]
            sent_array = file[11]

            return [summary, transcription, filename, summary_html, link, time, teacher, client_email, client_name, sent, precise_time, sent_array]
        
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

        return file
    
    cursor.close()
    db_conn.close()

    return "File not found!", 404
