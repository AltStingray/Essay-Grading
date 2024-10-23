# coding: cp1252
import os
import io
import time
import dropbox_module
import assemblyAI
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
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

OPENAI_API_KEY = os.environ.get("N_OPENAI_API_KEY")

FLASK_SESSION_SECRET = os.environ.get("FLASK_SESSION_SECRET")


# Web application fundament
app = Flask(__name__)

app.secret_key = FLASK_SESSION_SECRET

app.config['SESSION_TYPE'] = 'redis'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

q = Queue(connection=conn)

delete_data_from_table(id=3)

#db("create") #can be used to create postgres table only for the first time; to make update to an existing table or to delete it


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
        return render_template('results.html')
    else:
        time.sleep(1)
        return render_template('processing.html')

has_executed = False # Global flag

@app.route('/download', methods=["GET"])
def download():
    global has_executed

    def retrieve(result):

        file_object = io.BytesIO()
        file_object.write(result.encode('utf-8'))
        file_object.seek(0)

        return file_object
            
        
    job_id = session["job_id"]

    job = Job.fetch(job_id, connection=conn)

    result = job.return_value()

    if not has_executed:
        db_store(result[0], result[1])
        has_executed = True

    summary_report = retrieve(result[0])
    transcription = retrieve(result[1])

    pick_one = request.args.get("pick_one")

    if pick_one == "Summary report.odt":
        return send_file(summary_report, as_attachment=True, download_name="summary_report.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif pick_one == "Transcription.odt":
        return send_file(transcription, as_attachment=True, download_name="transcription.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif pick_one == "Summary_report.docx":
        return send_file(summary_report, as_attachment=True, download_name="summary_report.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif pick_one == "Transcription.docx":
        return send_file(transcription, as_attachment=True, download_name="transcription.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif pick_one == "Summary report.pdf":
        return send_file(pdf(result[0]), as_attachment=True, download_name="summary_report.pdf", mimetype="application/pdf")
    else:
        return send_file(pdf(result[1]), as_attachment=True, download_name="transcription.pdf", mimetype="application/pdf")


@app.route('/history')
def history():

    ids = db_get_ids()

    return render_template("history.html", ids=ids)

@app.route('/logs_download/<int:id>/<name>')
def logs_download(id, name):

    logs = db_retrieve(file_id=id)

    if name == "Summary report.odt":
        return send_file(logs[0], as_attachment=True, download_name=f"summary_report.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif name == "Transcription.odt":
        return send_file(logs[1], as_attachment=True, download_name=f"transcription.odt", mimetype="application/vnd.oasis.opendocument.text")
    elif name == "Summary report.pdf":
        return send_file(pdf(logs[0]), as_attachment=True, download_name=f"summary_report.pdf", mimetype="application/pdf")
    elif name == "Transcription.pdf":
        return send_file(pdf(logs[1]), as_attachment=True, download_name=f"transcription.pdf", mimetype="application/pdf")
    else:
        return logs
    

@app.route('/grading')
def grading():

    text = request.args.get("text")

    prompt = "You are an IETLS teacher that provides feedback on candidate's essays. In the section 'Grammar Mistakes' you point out grammar mistakes and in the section 'Improvement Suggestions' you provide improvement suggestions on the candidate's essay. Mark mistakes with the red color, cross line and red highlight color; display the correct words beside them with a green color and a green highlight color. The same way display punctuation mistakes. Make a pop-up window appear once clicked on the wrong word. The information in the pop-up window have to address the mistake. This should be accomplished in HTML format. After it provide the corrected version of the essay. Next, provide candidate with the feedback based on the following parameters, where parameters are bold and feedback is green colored: Task Fulfillment, Relevance & Completeness of Information, Grammatical Usage, Vocabulary Usage, Connections & Coherence, Connection between Lecture & Reading. "
    
    #grade = OpenAI(prompt, text)

    return render_template('grading.html')

#@app.route('/')

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

    if user_prompt != None:
        prompt = user_prompt
    else:
        prompt = "I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine. Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a table with 2 columns called areas that you are doing well and areas that you need to improve. The output text will be stored in a docx format file, so make the table relevant to this format. You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters." 

    summary_report = OpenAI(prompt, transcription)

    #Saving results
    f_list = [summary_report, transcription]

    return f_list


def OpenAI(prompt, content):

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

    pdf_file = io.BytesIO()

    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = []

    width, height = letter

    #c.setFont("Helvetica", 11)

    decoded_text = text.getvalue().decode("utf-8", errors="replace")

    flowables.append(Paragraph(decoded_text, styles["Normal"]))

    #y_position = height - 40
    #for line in decoded_text.split('\n'):
    #    if y_position <= 40: # add new page
    #        c.showPage()
    #        c.setFont("Helvetica", 11)
    #        y_position = height - 40
    #    c.drawString(40, y_position, line)
    #    y_position -= 15

    #c.save()

    doc.build(flowables)

    pdf_file.seek(0)

    return pdf_file



# These two lines tell Python to start Flask’s development server when the script is executed from the command line. 
# It’ll be used only when you run the script locally.
if __name__ == "__main__":

    app.run(host="127.0.0.1", port=8080, debug=True)
    
