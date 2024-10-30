# coding: cp1252
import os
import io
import time
import dropbox_module
import assemblyAI
import json
from rq import Queue
from rq.job import Job
from worker import conn
from flask import Flask, request, render_template, url_for, redirect, send_file, session
from markupsafe import escape
from moviepy.editor import *
from openai import OpenAI
from db_postgres import *
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date

OPENAI_API_KEY = os.environ.get("N_OPENAI_API_KEY")

FLASK_SESSION_SECRET = os.environ.get("FLASK_SESSION_SECRET")


# Web application fundament
app = Flask(__name__)

app.secret_key = FLASK_SESSION_SECRET

app.config['SESSION_TYPE'] = 'redis'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

q = Queue(connection=conn)

#db("create")
#db("delete_data")
#db("alter")
db("print")


@app.route('/') #Use the route() decorator to bind a function to a URL.
def index():
    
    return render_template('index.html')


@app.route('/summary_report')
def summary_report():

    return render_template('summary_report.html', name="start")


@app.route('/authorize')
def authorize():

    return redirect(dropbox_module.redirect_link)


@app.route('/start')
def start():
    
    auth_code = str(escape(request.args.get("code")))

    access_token = dropbox_module.authorization(auth_code)

    session["access_token"] = access_token

    return render_template('summary_report.html', name="choice")


@app.route('/choice')
def choice():

    choice = str(escape(request.args.get("choice", "")))

    if choice == "Own":
        return redirect(url_for('own'))
    else:
        return render_template('summary_report.html', name="link")
    

@app.route('/own')
def own():
    
    return render_template('summary_report.html', name="prompt")


@app.route('/default')
def default():

    prompt = request.args.get("prompt")

    session["prompt"] = prompt
    
    return render_template('summary_report.html', name="link")


@app.route('/processing', methods=["GET", "POST"])
def processing():
    
    link = request.args.get("link")

    access_token = session.get("access_token")
    
    prompt = session.pop("prompt", None) # because of the pop() this line won't trigger TypeError. It deletes the value in a session and returns it. Specified None here means that the value of "prompt" key doesn't matter. If the value is None or Str - doesn't matter.

    job = q.enqueue(main, link, access_token, prompt) # enque main function and it's parameters to execute in the background

    job_id=job.get_id() # get id of the job that is in process 

    session["job_id"] = job_id

    return redirect(url_for("results"))


@app.route('/results', methods=["GET", "POST"])
def results():

    job_id = session["job_id"]

    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:

        job = Job.fetch(job_id, connection=conn)

        result = job.return_value()

        if result[0].startswith("```python"):
            result = result[0].replace("```python\n", "").strip()
        else:
            result = result[0].replace("```\n", "").replace("```", "").strip()
        
        print(result)

        summary_report = json.loads(result)

        db_store(summary_report["text"], result[1], result[2], summary_report["html"])

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

    summary_report = retrieve(json.loads(result[0])["text"])
    transcription = retrieve(result[1])
    filename = result[2]
    filename = filename.replace(".mp4", "")

    pick_one = request.args.get("pick_one")

    if pick_one == "Summary report.odt":
        return send_file(summary_report, as_attachment=True, download_name=f"summary_report_{filename}.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif pick_one == "Transcription.odt":
        return send_file(transcription, as_attachment=True, download_name=f"transcription_{filename}.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif pick_one == "Summary report.docx":
        return send_file(summary_report, as_attachment=True, download_name=f"summary_report_{filename}.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif pick_one == "Transcription.docx":
        return send_file(transcription, as_attachment=True, download_name=f"transcription_{filename}.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif pick_one == "Summary report preview":
        return render_template("preview_report.html", html=json.loads(result[0])["html"])

@app.route('/history')
def history():

    ids = db_get_ids()

    return render_template("history.html", ids=ids)

@app.route('/logs_download/<int:id>/<name>')
def logs_download(id, name):

    logs = db_retrieve(file_id=id)

    summary_report = logs[0]
    transcription = logs[1]
    filename = logs[2]

    if name == "Summary report.odt":
        return send_file(io.BytesIO(summary_report), as_attachment=True, download_name=f"summary_report_{filename}.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif name == "Transcription.odt":
        return send_file(io.BytesIO(transcription), as_attachment=True, download_name=f"transcription_{filename}.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif name == "Summary report.html":

        html = logs[3]

        if html != None:
            html_data = (html.tobytes().decode('utf-8')).strip("{ }")
        else:
            summary_report = (str(summary_report, "utf-8")) + "\n\n <em>AI-generated content may be inaccurate or misleading. Always check for accuracy</em>.\n"
            html_data = '<p>' + summary_report.replace('\n', '<br>') + '</p>'

        return render_template("preview_report.html", html=html_data)
    else:
        return logs
    

@app.route('/grading')
def grading():
    
    return render_template('grading.html')

@app.route('/grading/queue')
def grading_queue():

    text = request.args.get("text")
    
    prompt = "You are an IETLS teacher that provides feedback on a candidate's essays. You are given an essay text delimited by triple quotes. In the section 'Grammar Mistakes' you point out grammar mistakes and in the section 'Improvement Suggestions' you provide improvement suggestions. Mark grammar mistakes with a red underline. The same way display punctuation mistakes. Make a built-in box pop-up window appear once hover over with a cursor on the mistake(grammar or punctuation). The information in the pop-up window has to address the mistake, displaying the correct word/symbol in green first, then a description about the mistake. By clicking on the correct green word in the built-in pop-up window, the underline mistake word should be replaced with a correct one, and the red underline should disappear. With a light bland yellow colour highlight all repetitive words. With a light bland green colour highlight all linking words. Provide the fully corrected version of the essay below, without any marks, just a simple corrected text. Next, provide candidate with the feedback based on the following parameters, where the parameter words are bold and black and the feedback description is green colored: Task Fulfillment, Relevance & Completeness of Information, Grammatical Usage, Vocabulary Usage, Connections & Coherence, Connection between Lecture & Reading. Display the overall band score number based on the IELTS grading system as well. All of this should be accomplished in a correct and structured HTML format, so your response can be inserted into an html file to display on the webpage. Everything should be in a 14 font size."

    job_queue = q.enqueue(RunOpenAI, prompt, text)

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

    result = job.return_value()

    print(result)

    result = result.replace("```html", "")

    return render_template('grading.html', name="finish", result=result)



@app.route('/about')
def about():

    return render_template('about.html')

@app.route('/login')
def login():

    return render_template('login.html')

@app.route('/register')
def register():

    return render_template('register.html')


def main(link, access_token, user_prompt):

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

    today = date.today()

    if user_prompt != None:
        prompt = user_prompt
    else:
        prompt = f"I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine. At the beginning of the report specify the header title 'OET Speaking Mock Test Session's Summary'; below specify 'Date: {today}' and teacher's name(who act as a patient) coming from the dialogue analysis. Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a table with 2 columns called areas that you are doing well and areas that you need to improve. Add the following line at the end of the report in italic style: 'AI-generated content may be inaccurate or misleading. Always check for accuracy.' You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters. Provide two versions of the report. First one is a simple text respond. Second one is a structured HTML. Wrap those two versions as values in a single pure dictionary with the following keys: text and html. Do not include anything like 'json' that goes after and before the ``` at the beginning and at the end of your response."


    summary_report = RunOpenAI(prompt, transcription)

    filename = filename.replace(".mp4", "")

    f_list = [summary_report, transcription, filename]
    
    return f_list


def RunOpenAI(prompt, content):

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f'''{content}'''}],
        )
    
    response = response.choices[0].message.content #tapping into the content of response
    
    return response


def pdf(text):

    decoded_text = text.getvalue().decode("utf-8", errors="replace")

    pdf_file = io.BytesIO()
    c = canvas.Canvas(pdf_file, pagesize=letter)
    c.setFont("Helvetica", 12)
    width, height = letter

    left_margin = 40
    right_margin = width - 40
    top_margin = height - 40
    bottom_margin = 40
    y_position = top_margin

    for line in decoded_text.split('\n'):

        if y_position <= bottom_margin: # add new page
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = top_margin
        c.drawString(left_margin, y_position, line)

        y_position -= 15

    c.save()

    pdf_file.seek(0)

    return pdf_file



# These two lines tell Python to start Flask’s development server when the script is executed from the command line. 
# It’ll be used only when you run the script locally.
if __name__ == "__main__":

    app.run(host="127.0.0.1", port=8080, debug=True)
    
