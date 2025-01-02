# coding: cp1252
import os
import io
import time
import dropbox_module
from main_python import *
from email_to import send_email
from openai_tools import *
from rq import Queue
from rq.job import Job
from rq.exceptions import NoSuchJobError
from worker import conn
from flask import Flask, request, render_template, url_for, redirect, send_file, session, jsonify
from markupsafe import escape
from db_postgres import *
from jinja2 import Template

PASSWORD = os.environ.get("CUSTOM_PROMPT_PASSWORD")
FLASK_SESSION_SECRET = os.environ.get("FLASK_SESSION_SECRET")
ENVIRONENT = os.environ.get("ENVIRONMENT")

if ENVIRONENT == "production":
    website_link = "https://benchmark-summary-report-eae227664887.herokuapp.com"
elif ENVIRONENT == "test":
    website_link = "https://benchmark-tools-test-env-99cb41517051.herokuapp.com"

# Web application fundament
app = Flask(__name__)

app.secret_key = FLASK_SESSION_SECRET

app.config['SESSION_TYPE'] = 'redis'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

q = Queue(connection=conn)

@app.route('/') #Use the route() decorator to bind a function to a URL.
def index():
    
    return render_template('index.html')

@app.route('/grading')
def grading():
    
    return render_template('grading.html')

@app.route('/grading/queue')
def grading_queue():

    topic = request.args.get("topic")

    essay = request.args.get("essay")

    submitted_by = request.args.get("submitted_by")

    job_queue = q.enqueue(run_essay_grading, topic, essay, submitted_by)

    job_id = job_queue.get_id()

    session["job_id_2"] = job_id

    return redirect(url_for("grading_processing"))

@app.route('/grading/processing')
def grading_processing():
    
    job_id = session["job_id_2"]

    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:

        job_result = job.return_value()

        result = job_result

        data = process_essay(result)

        db_store(data, "essay_logs")

        return redirect(url_for("grading_results"))
    else:
        time.sleep(1)
        return render_template('grading.html', name="wait", website=website_link)
    
@app.route('/grading/results')
def grading_results():

    show = request.args.get("show")

    job_id = session["job_id_2"]

    job = Job.fetch(job_id, connection=conn)

    job_result = job.return_value()

    result = job_result

    data = process_essay(result)

    if show == "linking-words":
        essay = data[12]
        words_category = "Linking Words"
    elif show == "repetitive-words":
        essay = data[13]
        words_category = "Repetitive Words"
    elif show == "corrected-essay":
        essay = data[14]
        words_category = "Corrected Essay"
    else:
        essay = data[11]
        words_category = "Grammar Mistakes"

    return render_template('grading.html', name="finish", topic=data[0], essay=essay, paragraphs_count=data[2], words_count=data[3], corrected_words=data[9], submitted_by=data[7], current_date=data[10], linking_words_count=data[5], repetitive_words_count=data[6], grammar_mistakes_count=data[4], band_score=data[8], id=0, words_category=words_category, route="grading_results")

@app.route('/grading/log')
def grading_logs():

    ids = db_get_ids(table_name="essay_logs")

    essays = []
    for id in ids:
        essay = {}
        db_value = db_retrieve(file_id=id, db="essay_logs")
        essay["id"] = id
        essay["date"] = db_value[10]
        essay["name"] = db_value[7].tobytes().decode('utf-8')
        essays.append(essay)

    return render_template("history.html", log="essay_grading", essays=essays)

@app.route('/grading/log/view/<int:id>')
def view_logs(id):

    show = request.args.get("show")
    
    logs = db_retrieve(file_id=id, db="essay_logs")

    topic = logs[0].tobytes().decode('utf-8')
    original_essay = logs[1].tobytes().decode('utf-8').strip("{ }")
    paragraphs_count = logs[2] 
    words_count = logs[3]
    grammar_mistakes_count = logs[4] 
    linking_words_count = logs[5] 
    repetitive_words_count = logs[6]
    submitted_by = logs[7].tobytes().decode('utf-8')
    band_score = logs[8] 
    sidebar_comments = [logs[9].strip("{ }").strip('"').replace('","', "")]
    current_date = logs[10]
    essay_grammar_mistakes = logs[11].tobytes().decode('utf-8')
    essay_linking_words = logs[12].tobytes().decode('utf-8')
    essay_repetitive_words = logs[13].tobytes().decode('utf-8')
    corrected_essay = logs[14].tobytes().decode('utf-8')

    if show == "linking-words":
        essay = essay_linking_words
        words_category = "Linking Words"
    elif show == "repetitive-words":
        essay = essay_repetitive_words
        words_category = "Repetitive Words"
    elif show == "corrected-essay":
        essay = corrected_essay
        words_category = "Corrected Essay"
    else:
        essay = essay_grammar_mistakes
        words_category = "Grammar Mistakes"

    return render_template('grading.html', name="finish", topic=topic, essay=essay, paragraphs_count=paragraphs_count, words_count=words_count, corrected_words=sidebar_comments, submitted_by=submitted_by, current_date=current_date, linking_words_count=linking_words_count, repetitive_words_count=repetitive_words_count, grammar_mistakes_count=grammar_mistakes_count, band_score=band_score, id=id, words_category=words_category, route="view_logs")


@app.route('/about')
def about():

    return render_template('about.html')

@app.route('/faq')
def faq():

    return render_template('faq.html')

@app.route('/login')
def login():

    return render_template('login.html')

@app.route('/register')
def register():

    return render_template('register.html')

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": f"Something went wrong: {error}"}), 500

# These two lines tell Python to start Flask’s development server when the script is executed from the command line. 
# It’ll be used only when you run the script locally.
if __name__ == "__main__":

    if ENVIRONENT == "production":
        app.run(host="127.0.0.1", port=8080, debug=False)
    elif ENVIRONENT == "test":
        app.run(host="127.0.0.1", port=5000, debug=True)
    
