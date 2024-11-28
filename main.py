# coding: cp1252
import os
import io
import re
import time
import dropbox_module
import assemblyAI
import json
from email_to import send_email
from openai_tools import *
from rq import Queue
from rq.job import Job
from worker import conn
from flask import Flask, request, render_template, url_for, redirect, send_file, session
from markupsafe import escape
from moviepy.editor import *
from openai import OpenAI
from db_postgres import *
from datetime import datetime
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
    fail = request.args.get("values", "")
    if fail:
        return render_template('summary_report.html', name="password", value="fail")
    else:
        return render_template('summary_report.html', name="password")
    
@app.route('/own')
def own():

    password = request.args.get("password", "")

    if password == None or password != PASSWORD:
        return redirect(url_for("password", values="fail"))
    else:
        default_prompt = "I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine.  Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a table with 2 columns called areas that you are doing well and areas that you need to improve."
        
        return render_template('summary_report.html', name="prompt", default_prompt=default_prompt)


@app.route('/custom_prompt')
def default():

    prompt = request.args.get("prompt")

    session["prompt"] = prompt
    
    return render_template('summary_report.html', name="link")


@app.route('/processing', methods=["GET", "POST"])
def processing():
    
    link = request.args.get("link")

    date = request.args.get("date")

    teacher_name = request.args.get("teacher")

    client_name = request.args.get("client")

    client_email = request.args.get("client_email")

    access_token = session.get("access_token")
    
    prompt = session.pop("prompt", None) # because of the pop() this line won't trigger TypeError. It deletes the value in a session and returns it. Specified None here means that the value of "prompt" key doesn't matter. If the value is None or Str - doesn't matter.

    job = q.enqueue(main, link, date, teacher_name, client_name, client_email, access_token, prompt) # enque main function and it's parameters to execute in the background

    job_id=job.get_id() # get id of the job that is in process 

    session["job_id"] = job_id

    return redirect(url_for("results"))


@app.route('/results', methods=["GET", "POST"])
def results():
    '''Waiting for the completion of the queried job.'''
    
    job_id = session["job_id"]

    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:

        job = Job.fetch(job_id, connection=conn)

        result = job.return_value()

        #print(result) # test

        strip_summary = strip(result)

        #print(strip_summary) # test

        summary_report = json.loads(strip_summary)

        filename = result[2].replace(".mp4", "")
        link = result[3]
        specified_date = result[4]
        teacher = result[5]
        client_email = result[6]
        client_name = result[7]

        if teacher == None or teacher == "":
            teacher = summary_report["teacher"]

        data = (summary_report["text"], result[1], filename, summary_report["html"], link, specified_date, teacher, client_email, client_name)

        db_store(data, "logs")

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

    strip_summary = strip(result)

    summary_report_text = retrieve(json.loads(strip_summary)["text"])
    summary_report_html = json.loads(strip_summary)["html"].strip("{ }")
    transcription = retrieve(result[1])
    filename = result[2]

    pick_one = request.args.get("pick_one")

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

    sort_by = request.args.get("sort_by")

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

    url = request.args.get("url")

    return redirect(url)

@app.route('/email_to')
def email_to():

    user_email = request.args.get("email")

    id = request.args.get("id")

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

    topic = result["original_topic"]
    original_text = result["original_text"]
    paragraphs_count = result["paragraphs_count"]
    grammar_mistakes = result["grammar_mistakes"]
    corrected_words = result["corrected_words"]
    submitted_by = result["submitted_by"]
    linking_words = result["linking_words"]
    repetitive_words = result["repetitive_words"]
    band_score = result["overall_band_score"]
    unnecessary_words = result["unnecessary_words"]
    current_date = datetime.now().strftime("%d-%m-%Y")
    words_count = len(original_text.split())

    grammar_mistakes_count = 0
    for n, word in enumerate(grammar_mistakes):
        re_word = re.search(word, original_text)
        print(re_word)
        try:
            if word == re_word.group():

                nums_str = ""
                for str_n in range(70):
                    nums_str += str(str_n)

                stripped_word = word.strip(nums_str)

                html_word = f"<span class='highlight' data-comment='comment{n + 1}'>{stripped_word}({n + 1})</span>" #<span class='jsx-1879403401'><div contenteditable='false' class='jsx-1879403401 hover'><div class='jsx-1879403401 hint'><div class='jsx-1879403401 title'>Correct article usage</div><div class='jsx-1879403401 suggestions'><div class='jsx-1879403401 suggestion'>the Atlantic</div></div><p class='jsx-1879403401 info'><p>It&nbsp;seems that there is&nbsp;an&nbsp;article usage problem here.</p></p><div class='jsx-1879403401 examples-button'>show examples</div></div></div></span>"
                original_text = original_text.replace(re_word.group(), html_word)
                grammar_mistakes_count += 1
        except AttributeError as err:
            print(err)

    print(original_text) # test

    #linking and repetitive words
    def count_and_replace(words, html_line, original_text, marker):
        words_count = 0
        already_exists = ""
        for word in words:
            if word in original_text:
                original_word = word
                print(f"Original word: {original_word}") # test
                html_word = html_line.format(original_word.strip(marker))
                print(html_word) # test
                original_text = original_text.replace(original_word, html_word)
                if word not in already_exists:
                    already_exists += word
                    words_count += 1
        return words_count, original_text

    linking_words_count, linking_original_text = count_and_replace(linking_words, "<span class='jsx-2885589388 linking-words'><div class='jsx-1879403401 root '><span contenteditable='false' class='jsx-1879403401 text'>{}</span><span class='jsx-1879403401'></span></div></span>", original_text, "#")
    repetitive_words_count, repetative_original_text = count_and_replace(repetitive_words, "<span class='jsx-2310580937 repeated-word'><div class='jsx-1879403401 root '><span contenteditable='false' class='jsx-1879403401 text'>{}</span><span class='jsx-1879403401'></span></div></span>", linking_original_text, "^")
    unnecessary_words_count, final_original_text = count_and_replace(unnecessary_words, "<span class='jsx-2310580937 unnecessary-word'><div class='jsx-1879403401 root '><span contenteditable='false' class='jsx-1879403401 text'>{}</span><span class='jsx-1879403401'></span></div></span>", repetative_original_text, "-")

    result_text = final_original_text

    print(f"\n\n{result_text}\n\n") # test

    sidebar_comments = []

    for n, word in enumerate(corrected_words):
        word_split = word.split()
        cache_word_split = word_split[:]
        correct_word = ""
        description = ""
        for one in range(len(cache_word_split)):
            if cache_word_split[one].startswith('('):
                description += (" ".join(word_split))
                break
            else:
                correct_word += (f"{word_split.pop(0)} ")

        html_line = f"<div id='comment{n + 1}' class='comment-box'><strong>({n + 1})</strong> <span class='green'>{correct_word}</span> <em>{description}</em></div>"
        
        sidebar_comments.append(html_line)
    
    data = (topic, result_text, paragraphs_count, words_count, grammar_mistakes_count, linking_words_count, repetitive_words_count, submitted_by, band_score, sidebar_comments, current_date, unnecessary_words_count)
    
    db_store(data, "essay_logs")

    return render_template('grading.html', name="finish", topic=topic, essay=result_text, paragraphs_count=paragraphs_count, words_count=words_count, corrected_words=sidebar_comments, submitted_by=submitted_by, current_date=current_date, linking_words_count=linking_words_count, repetitive_words_count=repetitive_words_count, grammar_mistakes_count=grammar_mistakes_count, band_score=band_score, unnecessary_words_count=unnecessary_words_count)

@app.route('/grading/log')
def grading_logs():

    ids = db_get_ids(table_name="essay_logs")

    essays = []
    for id in ids:
        essay = {}
        one = db_retrieve(file_id=id, db="essay_logs")
        essay["id"] = id
        essay["date"] = one[10]
        essay["name"] = one[7].tobytes().decode('utf-8')
        essays.append(essay)

    return render_template("history.html", log="essay_grading", essays=essays)

@app.route('/grading/log/view/<int:id>')
def view_logs(id):

    logs = db_retrieve(file_id=id, db="essay_logs")
    
    print(logs) # test

    essay = logs[1]
    result_text = (essay.tobytes().decode('utf-8')).strip("{ }")

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

    print(sidebar_comments)

    return render_template('grading.html', name="finish", topic=topic, essay=result_text, paragraphs_count=paragraphs_count, words_count=words_count, corrected_words=sidebar_comments, submitted_by=submitted_by, current_date=current_date, linking_words_count=linking_words_count, repetitive_words_count=repetitive_words_count, grammar_mistakes_count=grammar_mistakes_count, band_score=band_score, unnecessary_words_count=unnecessary_words_count)

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


def main(link, specified_date, teacher_name, client_name, client_email, access_token, user_prompt):
    '''Main function of the summary report generation. It takes 5 paramethers: (1)dropboxlink, (2)specified date by the user,
    (3)specified teacher's name, (4)Dropbox access token to download the file, (5)Specified prompt by the user.'''

    #Downloading the video
    downloaded_video, filename = (dropbox_module.download_file(link, access_token))

    #Making a usable object out of the VideoFileClip(video) class
    video = VideoFileClip(downloaded_video.name)

    # Convert it into the audio file
    video.audio.write_audiofile("audio.mp3", bitrate="100k")

    print("\nProcessing the transcription of the given audio file, please wait...\n")

    transcription = assemblyAI.run() # Making a transcription

    #os.remove("video.mp3") # find out how to delete the video.mp3
    os.remove("audio.mp3")

    print("Transcription created, working on the summary report...")

    if specified_date != None and specified_date != "":
        pass
    else:
        specified_date = datetime.now().strftime("%d-%m-%Y")

    if user_prompt != None:
        prompt = user_prompt + f"At the beginning of the report specify the header title 'OET Speaking Mock Test Session's Summary'; below specify 'Date: {specified_date}' and teacher's name(who acts as a patient): '{teacher_name}'. If 'None' specified, get teacher name coming from the dialogue analysis. Add the following line at the end of the report in italic style: 'AI-generated content may be inaccurate or misleading. Always check for accuracy.' You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters. Provide two versions of the report. First one is a simple text respond. Second one is a structured HTML (Note: Do not include <style> tag). Wrap those two versions and teacher's name as values in a single dictionary with the following keys: text, html and teacher. Return the dictionary."
    else:
        prompt = f"I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine. At the beginning of the report specify the header title 'OET Speaking Mock Test Session's Summary'; below specify 'Date: {specified_date}' and teacher's name(who acts as a patient): '{teacher_name}'. If 'None' specified, get teacher name coming from the dialogue analysis. Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a table with 2 columns called areas that you are doing well and areas that you need to improve. Add the following line at the end of the report in italic style: 'AI-generated content may be inaccurate or misleading. Always check for accuracy.' You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters. Provide two versions of the report. First one is a simple text respond. Second one is a structured HTML (Note: Do not include <style> tag). Important: wrap those two versions and a teacher's name as values in a single dictionary with the following keys: text, html and teacher. Return the dictionary."

    summary_report = run_summary_report(prompt, transcription)

    filename = filename.replace(".mp4", "")

    f_list = [summary_report, transcription, filename, link, specified_date, teacher_name, client_email, client_name]
    
    return f_list
        


def strip(result):

    if result[0].startswith("```python"):
        stripped_text = result[0].replace("```python\n", "").replace("```", "").strip()
    elif result[0].startswith("```json"):
        stripped_text = result[0].replace("```json\n", "").replace("```", "").strip()
    else:
        stripped_text = result[0].replace("```\n", "").replace("```", "").strip()
    
    return stripped_text

# These two lines tell Python to start Flask’s development server when the script is executed from the command line. 
# It’ll be used only when you run the script locally.
if __name__ == "__main__":

    app.run(host="127.0.0.1", port=8080, debug=True)
    
