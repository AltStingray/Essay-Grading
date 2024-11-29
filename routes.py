# coding: cp1252
import os
import io
import time
import json
from main import *
from email_to import send_email
from openai_tools import *
from rq import Queue
from rq.job import Job
from worker import conn
from flask import Flask, request, render_template, url_for, redirect, send_file, session
from markupsafe import escape
from db_postgres import *
from jinja2 import Template

PASSWORD = os.environ.get("CUSTOM_PROMPT_PASSWORD")

FLASK_SESSION_SECRET = os.environ.get("FLASK_SESSION_SECRET")


# Web application fundament
app = Flask(__name__)

app.secret_key = FLASK_SESSION_SECRET

app.config['SESSION_TYPE'] = 'redis'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

q = Queue(connection=conn)

#delete_table("essay_logs")
#db("create")

db("delete_data")
db("alter")

db("print")


@app.route('/') #Use the route() decorator to bind a function to a URL.
def index():
    
    return render_template('index.html')


@app.route('/summary_report')
def summary_report():

    return render_template('summary_report.html', name="authorize")


@app.route('/authorize')
def authorize():

    auth_from = request.args.get("auth")

    if auth_from == "summary_logs":
        return redirect(dropbox_module.redirect_link_summary_logs)
    else:
        return redirect(dropbox_module.redirect_link_start)


@app.route('/start')
def start():
    
    auth_code = str(escape(request.args.get("code")))

    access_token = dropbox_module.authorization(auth_code, "start")

    session["access_token"] = access_token

    return render_template('summary_report.html', name="choice")

@app.route('/skip_choice')
def skip_choice():

    auth_code = str(escape(request.args.get("code")))

    access_token = dropbox_module.authorization(auth_code, "skip_choice")

    session["access_token"] = access_token

    return redirect('/choice')

@app.route('/choice')
def choice():

    choice = str(escape(request.args.get("choice", "")))

    if choice == "Custom GPT Prompt":
        return redirect(url_for('password'))
    else:
        return render_template('summary_report.html', name="link")
    
@app.route('/password')
def password():
    fail = escape(request.args.get("values", ""))
    if fail:
        return render_template('summary_report.html', name="password", value="fail")
    else:
        return render_template('summary_report.html', name="password")
    
@app.route('/own')
def own():

    password = escape(request.args.get("password", ""))

    if password == None or password != PASSWORD:
        return redirect(url_for("password", values="fail"))
    else:
        default_prompt = "I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine.  Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a table with 2 columns called areas that you are doing well and areas that you need to improve."
        
        return render_template('summary_report.html', name="prompt", default_prompt=default_prompt)


@app.route('/custom_prompt')
def default():

    prompt = escape(request.args.get("prompt"))

    session["prompt"] = prompt
    
    return render_template('summary_report.html', name="link")


@app.route('/processing', methods=["GET", "POST"])
def processing():
    
    process = escape(request.args.get("process_in_background"))

    link = escape(request.args.get("link"))

    date = escape(request.args.get("date"))

    teacher_name = escape(request.args.get("teacher"))

    client_name = escape(request.args.get("client"))

    client_email = escape(request.args.get("client_email"))

    access_token = escape(session.get("access_token"))
    
    prompt = session.pop("prompt", None) # because of the pop() this line won't trigger TypeError. It deletes the value in a session and returns it. Specified None here means that the value of "prompt" key doesn't matter. If the value is None or Str - doesn't matter.

    job = q.enqueue(main_summary_report, link, date, teacher_name, client_name, client_email, access_token, prompt) # enque main function and it's parameters to execute in the background

    job_id=job.get_id() # get id of the job that is in process 

    session["job_id"] = job_id

    if not process:
        return redirect(url_for("results"))


@app.route('/results', methods=["GET", "POST"])
def results():
    '''Waiting for the completion of the queried job.'''
    
    job_id = session["job_id"]

    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:
        return render_template('results.html')
    else:
        time.sleep(1)
        return render_template('processing.html')

@app.route('/download', methods=["GET"])
def download():

    def retrieve(result):

        file_object = io.BytesIO()
        file_object.write(result.encode('utf-8'))
        file_object.seek(0)

        return file_object
            
    job_id = session["job_id"]

    job = Job.fetch(job_id, connection=conn)

    result = job.return_value()

    strip_summary = strip_text(result)

    summary_report_text = retrieve(json.loads(strip_summary)["text"])
    summary_report_html = json.loads(strip_summary)["html"].strip("{ }")
    transcription = retrieve(result[1])
    filename = result[2]

    pick_one = escape(request.args.get("pick_one"))

    if pick_one == "Summary report.odt":
        return send_file(summary_report_text, as_attachment=True, download_name=f"summary_report_{filename}.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif pick_one == "Transcription.odt":
        return send_file(transcription, as_attachment=True, download_name=f"transcription_{filename}.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif pick_one == "Summary report.docx":
        return send_file(summary_report_text, as_attachment=True, download_name=f"summary_report_{filename}.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif pick_one == "Transcription.docx":
        return send_file(transcription, as_attachment=True, download_name=f"transcription_{filename}.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif pick_one == "Summary report preview":
        return render_template("preview_report.html", html=summary_report_html)

@app.route('/summary/log')
def history():
    '''Displaying the logs of the submitted summary reports'''

    sort_by = escape(request.args.get("sort_by"))

    ids = db_get_ids(table_name="Logs")

    reports = []

    for id in ids:

        report_dict = {}

        logs = db_retrieve(file_id=id, db="Logs")

        report_dict.update({"id": id})
        report_dict.update({"url": logs[4]})
        report_dict.update({"date": logs[5]})
        report_dict.update({"teacher": logs[6]})
        report_dict.update({"client_email": logs[7]})
        report_dict.update({"client_name": logs[8]})
        report_dict.update({"sent": logs[9]})

        reports.append(report_dict)

    if sort_by == "high-low":

        def high_low(e):
            
            return e["id"]
        
        reports.sort(reverse=True, key=high_low)
        
        return render_template("history.html", log="summary_report", reports=reports, sort_by="High-Low")
    
    elif sort_by == "date-new":

        def sort_by_new(e):

            return e["date"]
        
        reports.sort(reverse=True, key=sort_by_new)

        return render_template("history.html", log="summary_report", reports=reports, sort_by="Date-New")
    
    elif sort_by == "date-old":

        def sort_by_new(e):

            return e["date"]
        
        reports.sort(key=sort_by_new)

        return render_template("history.html", log="summary_report", reports=reports, sort_by="Date-Old")
    else:

        def low_high(e):
            
            return e["id"]
        
        reports.sort(key=low_high)

        return render_template("history.html", log="summary_report", reports=reports, sort_by="Low-High")

@app.route('/logs_download/<id>/<name>')
def logs_download(id, name):

    logs = db_retrieve(file_id=id, db="Logs")

    summary_report = logs[0]
    transcription = logs[1]
    filename = logs[2]
    html = logs[3]

    if name == "Transcription.odt":
        return send_file(io.BytesIO(transcription), as_attachment=True, download_name=f"transcription_{filename}.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif name == "Summary report.html":

        html_data = (html.tobytes().decode('utf-8')).strip("{ }") #decoding the memory value from database into a string

        return render_template("preview_report.html", html=html_data)
    else:
        return logs

@app.route('/redirect')
def redirect_to():

    url = escape(request.args.get("url"))

    return redirect(url)

@app.route('/email_to')
def email_to():

    user_email = escape(request.args.get("email"))

    id = escape(request.args.get("id"))

    logs = db_retrieve(file_id=id, db="Logs")

    #plain_text = (str(logs[0], "utf-8"))

    date = datetime.now().strftime("%d-%m-%Y")

    summary_report = (logs[3].tobytes().decode('utf-8')).strip("{ }")

    with open("templates/email_template.html", "r", encoding="utf-8") as file:
        template = Template(file.read())

        html = template.render(
            summary_report_content=summary_report,
            date=date
        )

    send_email(user_email, html)

    sent_email(id)

    return redirect("/summary/log")

@app.route('/grading')
def grading():
    
    return render_template('grading.html')

@app.route('/grading/queue')
def grading_queue():

    topic = escape(request.args.get("topic"))

    essay = escape(request.args.get("essay"))

    submitted_by = escape(request.args.get("submitted_by"))

    job_queue = q.enqueue(run_essay_grading, topic, essay, submitted_by)

    job_id = job_queue.get_id()

    session["job_id_2"] = job_id

    return redirect(url_for("grading_processing"))

@app.route('/grading/processing')
def grading_processing():
    
    job_id = session["job_id_2"]

    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:
        return redirect(url_for("grading_results"))
    else:
        time.sleep(1)
        return render_template('grading.html', name="wait")
    
@app.route('/grading/results')
def grading_results():

    job_id = session["job_id_2"]

    job = Job.fetch(job_id, connection=conn)

    job_result = job.return_value()

    result = job_result

    data = process_essay(result)

    db_store(data, "essay_logs")

    return render_template('grading.html', name="finish", topic=data[0], essay=data[1], paragraphs_count=data[2], words_count=data[3], corrected_words=data[9], submitted_by=data[7], current_date=data[10], linking_words_count=data[5], repetitive_words_count=data[6], grammar_mistakes_count=data[4], band_score=data[8], unnecessary_words_count=data[11])

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

    logs = db_retrieve(file_id=id, db="essay_logs")

    essay = logs[1].tobytes().decode('utf-8').strip("{ }")
    topic = logs[0].tobytes().decode('utf-8')
    paragraphs_count = logs[2] 
    words_count = logs[3]
    grammar_mistakes_count = logs[4] 
    linking_words_count = logs[5] 
    repetitive_words_count = logs[6]
    submitted_by = logs[7].tobytes().decode('utf-8')
    band_score = logs[8] 
    sidebar_comments = [logs[9].strip("{ }").strip('"').replace('","', "")]
    current_date = logs[10]
    unnecessary_words_count = logs[11]

    return render_template('grading.html', name="finish", topic=topic, essay=essay, paragraphs_count=paragraphs_count, words_count=words_count, corrected_words=sidebar_comments, submitted_by=submitted_by, current_date=current_date, linking_words_count=linking_words_count, repetitive_words_count=repetitive_words_count, grammar_mistakes_count=grammar_mistakes_count, band_score=band_score, unnecessary_words_count=unnecessary_words_count)

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

# These two lines tell Python to start Flask’s development server when the script is executed from the command line. 
# It’ll be used only when you run the script locally.
if __name__ == "__routes__":

    app.run(host="127.0.0.1", port=8080, debug=True)
    
