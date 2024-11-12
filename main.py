# coding: cp1252
import os
import io
import re
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
from datetime import date

OPENAI_API_KEY = os.environ.get("N_OPENAI_API_KEY")

PASSWORD = os.environ.get("CUSTOM_PROMPT_PASSWORD")

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


@app.route('/default')
def default():

    prompt = request.args.get("prompt")

    session["prompt"] = prompt
    
    return render_template('summary_report.html', name="link")


@app.route('/processing', methods=["GET", "POST"])
def processing():
    
    link = request.args.get("link")

    date = request.args.get("date")

    teacher_name = request.args.get("teacher")

    access_token = session.get("access_token")
    
    prompt = session.pop("prompt", None) # because of the pop() this line won't trigger TypeError. It deletes the value in a session and returns it. Specified None here means that the value of "prompt" key doesn't matter. If the value is None or Str - doesn't matter.

    job = q.enqueue(main, link, date, teacher_name, access_token, prompt) # enque main function and it's parameters to execute in the background

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

        strip_summary = strip(result)

        summary_report = json.loads(strip_summary)

        filename = result[2].replace(".mp4", "")

        data = (summary_report["text"], result[1], filename, summary_report["html"])

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

@app.route('/history')
def history():

    ids = db_get_ids(table_name="Logs")

    return render_template("history.html", log="summary_report", ids=ids)

@app.route('/logs_download/<int:id>/<name>')
def logs_download(id, name):

    logs = db_retrieve(file_id=id, db="Logs")

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
            html_data = (html.tobytes().decode('utf-8')).strip("{ }") #decoding the memory value from database into a string
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

    topic = request.args.get("topic")

    essay = request.args.get("essay")

    submitted_by = request.args.get("submitted_by")

    essay = f"The topic of the essay: {topic}.\nThe essay: {essay} \nSubmitted by: {submitted_by}"
    
    #"corrected_text": "corrected_text",
    example_results_dict = {
        "original_topic": "original_topic",
        "original_text": "original_text",
        "paragraphs_count": "paragraphs_count",
        "grammar_mistakes": ["!list!", "!of!", "!words!", "!that!", "!contain!", "!a!", "!mistake!", "!which!", "!are!", "!delemited!", "!by!", "!", "!mark!"],
        "corrected_words": ["corrected", "version", "of", "the", "words", "with", "the", "(grammar rule reason)"],
        "linking_words": ["#list#", "#of#", "#all#", "#linking#", "#words#"],
        "repetitive_words": ["^list^", "^of^", "^all^", "^repetitive^", "^words^"],
        "unnecessary_words": ["-list-", "-of-", "-all-", "-unnecessary-", "-words-"],
        "submitted_by": "submitted_by",
        "overall_band_score": "overall_band_score(float value)",
    }

    prompt = f'''
    Introduction: You are an IETLS teacher that provides feedback on a candidate's essays. 
    You are given a topic and an essay text based on this topic delimited by triple quotes. 
    Provide the grading based on the IELTS standards. 

    Instruction:
    Structure your answer in one dictionary with different values as demonstrated in the following dictionary example: {example_results_dict}.
    In the given example dictionary, each column/key and its value describes what it should contain, in which format and how every word should be wrapped.
    One of your main tasks is to enclose/wrap all the words from example dictionary's lists with the specific mark described in the steps below, either '!', '#', '^' or '-' - in the 'original_text'. I'll repeat again - specific words in 'original_text' should be enclosed/wrapped.
    Every word placed in a list should exactly match word in the 'original_text', either it's lower or upper case, and it should be marked/enclosed properly as well.
    Enclose the dict, all of the keys and values into double quotes, not single.

    Do not rush with the answer. Take your time and process each of the following steps sequentially.
    
    Step 1 - In the 'original_text' find all of the words that contain grammar mistake and wrap them with the '!' mark. If one mistake contains multiple words, enclose them with a single pair of '!' mark.

    Step 2 - Store all of the found grammar mistakes into the 'grammar_mistakes' list wrapped with the '!'.
     
    Step 3 - In the 'original_text' find all of the linking words and wrap them with the '#' mark. If linking word contains punctuation sign, just separate them with one whitespace and wrap the linking word with '#'.
    Linking words definition: Linking words, also known as transition words, are words and phrases like 'however' or 'on the other hand' that connect clauses, sentences, paragraphs, or other words.

    Step 4 - Store all of the found linking words into the 'linking_words' list wrapped with the '#'. 
     
    Step 5 - In the 'original_text' find all of the repetitive words and wrap them with the '^' mark. If not single word but sentence gets repeated many times wrap it with the '^' mark(i.e. ^social media^).

    Step 6 - Store all of the found repetitive words into the 'repetitive_words' list wrapped with the '^'.  
    
    Step 7 - In the 'original_text' find all of the unnecessary words and wrap them with the '-' mark. 

    Step 8 - Store all of the found unnecessary words into the 'unnecessary_words' list wrapped with the '-'. 

    '''

    job_queue = q.enqueue(RunOpenAI, prompt, essay)

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

    if job_result.startswith("```"):
        result = strip([job_result])
    else:
        result = job_result

    result = json.loads(result)

    print(result)

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
    current_date = date.today()
    words_count = len(original_text.split())

    grammar_mistakes_count = 0
    for n, word in enumerate(grammar_mistakes):
        re_word = re.search(word, original_text)
        print(re_word)
        if word == re_word.group():
            html_word = f"<span class='highlight' data-comment='comment{n + 1}'>{word.strip("!")}({n + 1})</span>" #<span class='jsx-1879403401'><div contenteditable='false' class='jsx-1879403401 hover'><div class='jsx-1879403401 hint'><div class='jsx-1879403401 title'>Correct article usage</div><div class='jsx-1879403401 suggestions'><div class='jsx-1879403401 suggestion'>the Atlantic</div></div><p class='jsx-1879403401 info'><p>It&nbsp;seems that there is&nbsp;an&nbsp;article usage problem here.</p></p><div class='jsx-1879403401 examples-button'>show examples</div></div></div></span>"
            original_text = original_text.replace(re_word.group(), html_word)
            grammar_mistakes_count += 1

    print(original_text)

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
    print(f"\n\n{result_text}\n\n")

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

        html_line = f'<div id="comment{n + 1}" class="comment-box"><strong>({n + 1})</strong> <span class="green">{correct_word}</span> <em>{description}</em></div>'
        
        sidebar_comments.append(html_line)
    
    data = (topic, result_text, paragraphs_count, words_count, grammar_mistakes_count, linking_words_count, repetitive_words_count, submitted_by, band_score, sidebar_comments, current_date, unnecessary_words_count)

    
    #db_store(data, "essay_logs")

    return render_template('grading.html', name="finish", topic=topic, essay=result_text, paragraphs_count=paragraphs_count, words_count=words_count, corrected_words=sidebar_comments, submitted_by=submitted_by, current_date=current_date, linking_words_count=linking_words_count, repetitive_words_count=repetitive_words_count, grammar_mistakes_count=grammar_mistakes_count, band_score=band_score, unnecessary_words_count=unnecessary_words_count)

@app.route('/grading/log')
def grading_logs():

    ids = db_get_ids(table_name="essay_logs")
    
    return render_template("history.html", log="essay_grading", ids=ids)

@app.route('/grading/log/view/<int:id>')
def view_logs():

    logs = db_retrieve(file_id=id, db="essay_logs")

    essay = logs[1]

    logs = io.BytesIO(logs)
    topic = logs[0]
    paragraphs_count = logs[2]
    words_count = logs[3]
    grammar_mistakes_count = logs[4]
    linking_words_count = logs[5]
    repetitive_words_count = logs[6]
    submitted_by = logs[7]
    band_score = logs[8]
    sidebar_comments = logs[9]
    current_date = logs[10]
    unnecessary_words_count = logs[11]

    result_text = (essay.tobytes().decode('utf-8')).strip("{ }")
    
    return render_template('grading.html', name="finish", topic=topic, essay=result_text, paragraphs_count=paragraphs_count, words_count=words_count, corrected_words=sidebar_comments, submitted_by=submitted_by, current_date=current_date, linking_words_count=linking_words_count, repetitive_words_count=repetitive_words_count, grammar_mistakes_count=grammar_mistakes_count, band_score=band_score, unnecessary_words_count=unnecessary_words_count)

@app.route('/about')
def about():

    return render_template('about.html')

@app.route('/login')
def login():

    return render_template('login.html')

@app.route('/register')
def register():

    return render_template('register.html')


def main(link, specified_date, teacher_name, access_token, user_prompt):

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

    if specified_date != None or specified_date != "":
        pass
    else:
        specified_date = date.today()

    if user_prompt != None:
        prompt = user_prompt + f"At the beginning of the report specify the header title 'OET Speaking Mock Test Session's Summary'; below specify 'Date: {specified_date}' and teacher's name(who acts as a patient): '{teacher_name}'. If 'None' specified, get teacher name coming from the dialogue analysis. Add the following line at the end of the report in italic style: 'AI-generated content may be inaccurate or misleading. Always check for accuracy.' You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters. Provide two versions of the report. First one is a simple text respond. Second one is a structured HTML. Wrap those two versions as values in a single pure dictionary with the following keys: text and html. Do not include anything like 'json' that goes after and before the ``` at the beginning and at the end of your response."
    else:
        prompt = f"I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine. At the beginning of the report specify the header title 'OET Speaking Mock Test Session's Summary'; below specify 'Date: {specified_date}' and teacher's name(who acts as a patient): '{teacher_name}'. If 'None' specified, get teacher name coming from the dialogue analysis. Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a table with 2 columns called areas that you are doing well and areas that you need to improve. Add the following line at the end of the report in italic style: 'AI-generated content may be inaccurate or misleading. Always check for accuracy.' You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters. Provide two versions of the report. First one is a simple text respond. Second one is a structured HTML. Important: wrap those two versions as values in a single dictionary with the following keys: text and html. Do not include anything like 'json' that goes after and before the ``` at the beginning and at the end of your response."


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


def strip(result):

    if result[0].startswith("```python"):
        strip_summary = result[0].replace("```python\n", "").replace("```", "").strip()
    elif result[0].startswith("```json"):
        strip_summary = result[0].replace("```json\n", "").replace("```", "").strip()
    else:
        strip_summary = result[0].replace("```\n", "").replace("```", "").strip()
    
    return strip_summary

# These two lines tell Python to start Flask’s development server when the script is executed from the command line. 
# It’ll be used only when you run the script locally.
if __name__ == "__main__":

    app.run(host="127.0.0.1", port=8080, debug=True)
    
