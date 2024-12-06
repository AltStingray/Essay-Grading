import os
import re
import assemblyAI
import dropbox_module
import json
from datetime import datetime
from moviepy.editor import *
from openai_tools import run_summary_report, strip_text
from db_postgres import db_store

def process_essay(result):

    topic = result["original_topic"]
    original_text = result["original_text"]
    submitted_by = result["submitted_by"]

    essay_grammar_mistakes = result["essay_grammar_mistakes"]
    grammar_mistakes = result["grammar_mistakes"]
    corrected_words = result["corrected_words"]

    essay_linking_words = result["essay_linking_words"]
    linking_words = result["linking_words"]

    essay_repetitive_words = result["essay_repetitive_words"]
    repetitive_words = result["repetitive_words"]

    essay_unnecessary_words = result["essay_unnecessary_words"]
    unnecessary_words = result["unnecessary_words"]

    corrected_essay = result["corrected_essay"]
    paragraphs_count = result["paragraphs_count"]
    band_score = result["overall_band_score"]

    current_date = datetime.now().strftime("%d-%m-%Y")
    words_count = len(original_text.split())

    grammar_mistakes_count = 0
    for n, word in enumerate(grammar_mistakes):

        re_word = re.search(word, essay_grammar_mistakes)
        print(re_word)

        try:
            if word == re_word.group():

                nums_str = ""
                for str_n in range(70):
                    nums_str += str(str_n)

                stripped_word = word.strip(nums_str)

                html_word = f"<span class='highlight' data-comment='comment{n + 1}'>{stripped_word}({n + 1})</span>"
                updated_essay_grammar_mistakes = essay_grammar_mistakes.replace(re_word.group(), html_word)
                grammar_mistakes_count += 1

        except AttributeError as err:
            print(err)

    #linking and repetitive words
    def count_and_replace(words, html_line, text, marker):

        words_count = 0
        already_exists = ""

        for word in words:
            
            if word in text:
                original_word = word

                print(original_word) #test

                html_word = html_line.format(original_word.strip(marker))

                updated_text = text.replace(original_word, html_word)
                
                if word not in already_exists:
                    already_exists += word
                    words_count += 1

        return words_count, updated_text

    linking_words_count, updated_essay_linking_words = count_and_replace(linking_words, "<span class='jsx-2885589388 linking-words'><div class='jsx-1879403401 root '><span contenteditable='false' class='jsx-1879403401 text'>{}</span><span class='jsx-1879403401'></span></div></span>", essay_linking_words, "#")
    repetitive_words_count, updated_essay_repetitive_words = count_and_replace(repetitive_words, "<span class='jsx-2310580937 repeated-word'><div class='jsx-1879403401 root '><span contenteditable='false' class='jsx-1879403401 text'>{}</span><span class='jsx-1879403401'></span></div></span>", essay_repetitive_words, "^")
    unnecessary_words_count, updated_essay_unnecessary_words = count_and_replace(unnecessary_words, "<span class='jsx-2310580937 unnecessary-word'><div class='jsx-1879403401 root '><span contenteditable='false' class='jsx-1879403401 text'>{}</span><span class='jsx-1879403401'></span></div></span>", essay_unnecessary_words, "-")

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
    
    data = (topic, original_text, paragraphs_count, words_count, grammar_mistakes_count, linking_words_count, repetitive_words_count, submitted_by, band_score, sidebar_comments, current_date, unnecessary_words_count, updated_essay_grammar_mistakes, updated_essay_linking_words, updated_essay_repetitive_words, updated_essay_unnecessary_words, corrected_essay)
    
    return data

def main_summary_report(link, specified_date, teacher, client_name, client_email, access_token, user_prompt):
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

    print(specified_date) # test

    if specified_date == None or specified_date == "":
        print("Date is absent")
        specified_date = datetime.now().strftime("%d-%m-%Y")

    if user_prompt != None:
        prompt = user_prompt + f"At the beginning of the report specify the header title 'OET Speaking Mock Test Session's Summary'; below specify 'Date: {specified_date}' and teacher's name(who acts as a patient): '{teacher}'. If 'None' specified, get teacher name coming from the dialogue analysis. Add the following line at the end of the report in italic style: 'AI-generated content may be inaccurate or misleading. Always check for accuracy.' You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters. Provide two versions of the report. First one is a simple text respond. Second one is a structured HTML (Note: Do not include <style> tag). Wrap those two versions and teacher's name as values in a single dictionary with the following keys: text, html and teacher. Return the dictionary."
    else:
        prompt = f"I run an online OET speaking mock test service where candidates act as doctors, nurses or other medical practitioners and practice roleplay scenarios with a teacher who acts as the patient or the patient's relative. After each session, we provide a detailed report to the candidate, highlighting their performance. You are given a dialogue text delimited by triple quotes on the topic of medicine. At the beginning of the report specify the header title 'OET Speaking Mock Test Session's Summary'; below specify 'Date: {specified_date}' and teacher's name(who acts as a patient): '{teacher}'. If 'None' specified, get teacher name coming from the dialogue analysis. Please summarise the teacher's feedback on the candidate's grammar, lexical choices, pronunciation, and overall communication skills. In the overall communication skills section, use the five categories in the clinical communication criteria table in the knowledge file delimited by triple quotes. Summarise the teacher's feedback on the candidate's performance. Structure the report with sections for each roleplay and an overall performance summary which includes a bordered table with 2 columns called areas that you are doing well and areas that you need to improve; make the text font in table bigger and the table itself wider. Add the following line at the end of the report in italic style and very small font size, a little bit transparent: 'AI-generated content may be inaccurate or misleading. Always check for accuracy.' You are not limited by a particular range of words, so provide detailed report with at least 4000 charaters. Provide two versions of the report. First one is a simple text respond. Second one is a structured HTML (Note: Do not include <style> tag). Important: wrap those two versions and a teacher's name as values in a single dictionary with the following keys: text, html and teacher. Return the dictionary."

    summary_report = run_summary_report(prompt, transcription)

    filename = filename.replace(".mp4", "")

    strip_summary = strip_text(summary_report)
    
    summary_report = json.loads(strip_summary)

    print(teacher)
    
    if teacher == "":
        print("lol") # test
        teacher = summary_report["teacher"]

    data = (summary_report["text"], transcription, filename, summary_report["html"], link, specified_date, teacher, client_email, client_name)

    db_store(data, "logs")

    return data