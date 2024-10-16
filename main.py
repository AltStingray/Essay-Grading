# coding: cp1252
import os
import io
import time
import dropbox_module
import assemblyAI
from rq import Queue
from rq.job import Job
from worker import conn
from flask import Flask, request, render_template, url_for, redirect, send_file, send_from_directory, jsonify, session
from markupsafe import escape
from moviepy.editor import *
from openai import OpenAI
from werkzeug.utils import secure_filename

q = Queue(connection=conn)

# Web application fundament
app = Flask(__name__)

app.secret_key = "32I4g1&g%J+*2o)"

app.config['SESSION_TYPE'] = 'redis'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

@app.route('/') #Use the route() decorator to bind a function to a URL.
def index():
    
    return render_template('index.html', name="start")


@app.route('/authorize')
def authorize():

    return redirect(dropbox_module.redirect_link)


@app.route('/start')
def start():
    
    auth_code = str(escape(request.args.get("code")))

    access_token = dropbox_module.authorization(auth_code)

    session["access_token"] = access_token

    return render_template('index.html', name="choice")


@app.route('/choice')
def choice():

    choice = str(escape(request.args.get("choice", "")))

    if choice == "Own":
        return redirect(url_for('own'))
    else:
        return render_template('index.html', name="link")
    

@app.route('/own')
def own():
    
    return render_template('index.html', name="prompt")

@app.route('/default')
def default():

    prompt = request.args.get("prompt")

    session["prompt"] = prompt
    
    return render_template('index.html', name="link")

@app.route('/processing', methods=["GET", "POST"])
def processing():
    
    link = request.args.get("link")

    access_token = session.get("access_token")
    
    try:
        prompt = session["prompt"]
    except: KeyError

    if prompt != None:
        pass
    else:
        prompt = ""
    job = q.enqueue(main, link, access_token, prompt) # enque is working

    session.pop("prompt", None)

    job_id=job.get_id() #okay, we're getting id

    session["job_id"] = job_id

    return redirect(url_for("results"))


@app.route('/results', methods=["GET", "POST"])
def results():

    job_id = session["job_id"]

    job = Job.fetch(job_id, connection=conn)

    if job.is_finished:

        return render_template('results.html')
    else:
        time.sleep(1)
        return render_template('processing.html')

@app.route('/download', methods=["GET"])
def download_summary():

    job_id = session["job_id"]

    job = Job.fetch(job_id, connection=conn)

    result = job.return_value()

    pick_one = request.args.get("pick_one")

    if pick_one == "Summary report":

        file_object = io.BytesIO()
        file_object.write(result[0].encode('utf-8'))
        file_object.seek(0)

        return send_file(file_object, as_attachment=True, download_name="summary_report.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        file_object = io.BytesIO()
        file_object.write(result[1].encode('utf-8'))
        file_object.seek(0)

        return send_file(file_object, as_attachment=True, download_name="transcription.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.route('/about')
def about():

    return render_template('about.html')

@app.route("/teacher's")
def teacher():

    return render_template("teacher's.html")

@app.route("/candidate's")
def candidate():

    return render_template("candidate's.html")

@app.route('/history')
def history():

    return render_template("history.html")

@app.route('/login')
def login():

    return render_template('login.html')

@app.route('/register')
def register():

    return render_template('register.html')

def main(link, access_token, user_prompt):

    #Downloading the video
    downloaded_video = (dropbox_module.download_file(link, access_token))

    #Making a usable object out of the VideoFileClip(video) class
    video = VideoFileClip(downloaded_video.name)

    # Convert it into the audio file
    video.audio.write_audiofile("audio.mp3", bitrate="100k")

    print("\nProcessing the transcription of the given audio file, please wait...\n")

    transcription = assemblyAI.run() # Making a transcription

    #os.remove("video.mp3") # find out how to delete the video.mp3
    os.remove("audio.mp3")

    print("Transcription created, working on the summary report...")

    #my key: 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
    # NP's: sk-xBdlGJMujfH_NsjBc0K3ym5tTLyEjJN3o-DaMLuYhgT3BlbkFJOvq20KiNWlZLAQN4yn03pECwsNb0b3oGnZ62Dd3WMA
    client = OpenAI(api_key="sk-xBdlGJMujfH_NsjBc0K3ym5tTLyEjJN3o-DaMLuYhgT3BlbkFJOvq20KiNWlZLAQN4yn03pECwsNb0b3oGnZ62Dd3WMA")

    if len(user_prompt) > 0:
        prompt = user_prompt
    else:
        prompt = "I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine. Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a table with 2 columns called areas that you are doing well and areas that you need to improve. The output text will be stored in a docx format file, so make the table relevant to this format. You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters." 

    summary_report = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f'''{transcription}'''}],
        )
    
    summary_report = summary_report.choices[0].message.content #tapping into the content of response

    #Saving results
    f_list = [summary_report, transcription]

    return f_list


# These two lines tell Python to start Flask’s development server when the script is executed from the command line. 
# It’ll be used only when you run the script locally.
if __name__ == "__main__":

    app.run(host="127.0.0.1", port=8080, debug=True)
    