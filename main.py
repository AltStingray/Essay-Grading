# coding: cp1252
import os
import time
import dropbox_module
import assemblyAI
from rq import Queue
from rq.job import Job
from worker import conn
from flask import Flask, request, render_template, url_for, redirect, send_file, jsonify, session
from markupsafe import escape
from moviepy.editor import *
from openai import OpenAI

username = (os.getenv("userprofile"))[9:]

q = Queue(connection=conn)

# Web application fundament
app = Flask(__name__)

app.secret_key = b"32I4g1&g%J+*2o)"

app.config['SESSION_TYPE'] = 'redis'

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

    session["access_token", ] = access_token

    dropbox_module.store(access_token, "access_token")

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

data = []
@app.route('/default')
def default():

    prompt = request.args.get("prompt")
    data.append(prompt)
    
    return render_template('index.html', name="link")

@app.route('/results', methods=["GET", "POST"])
def results():

    link = request.args.get("link")

    access_token = session.get("access_token")

    dropbox_module.store(link, "link")

    print("Okay")
    job = q.enqueue(main, link, access_token) # enque is working

    #time.sleep(5)

    job_id=job.get_id() #okay, we're getting id

    return render_template('results.html', name="processing", job_id=job_id)


@app.route('/main/<job_id>', methods=["GET", "POST"])
def processing(job_id):

    print(job_id)

    job = Job.fetch(job_id, connection=conn)
            
    if job.is_finished:
        result = jsonify(result=job.result)
        print(result)
        send_file(path_or_file=result, download_name="summary_report.docx", as_attachment=True)
        return "Job is finished!" + result
    else:
        return "Job is not finished yet.", 202

    return render_template('results.html', name="results")

    
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

def main(link, access_token):

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

    print("Transcription created, working on the summary report...\n")

    #my key: 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
    # NP's: sk-xBdlGJMujfH_NsjBc0K3ym5tTLyEjJN3o-DaMLuYhgT3BlbkFJOvq20KiNWlZLAQN4yn03pECwsNb0b3oGnZ62Dd3WMA
    client = OpenAI(api_key="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")
    
    if len(data) > 0:
        prompt = data[0]
    else:
        prompt = "I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine. Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a table with 2 columns called areas that you are doing well and areas that you need to improve. The output text will be stored in a docx format file, so make the table relevant to this format. You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters." 

    summary_report = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f'''{transcription}'''}],
        )
    print(summary_report)
    print(type(summary_report))

    #Saving results
    with open("summary_report.docx", "w") as file:
        file.write(summary_report)
    return summary_report


# These two lines tell Python to start Flask’s development server when the script is executed from the command line. 
# It’ll be used only when you run the script locally.
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
    