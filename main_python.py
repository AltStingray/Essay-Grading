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

    #essay_unnecessary_words = result["essay_unnecessary_words"]
    #unnecessary_words = result["unnecessary_words"]

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
                essay_grammar_mistakes = essay_grammar_mistakes.replace(re_word.group(), html_word)
                grammar_mistakes_count += 1

        except AttributeError as err:
            print(err)

    #print(essay_grammar_mistakes) # test

    #linking and repetitive words
    def count_and_replace(words, html_line, text, marker):

        words_count = 0
        already_exists = ""

        for word in words:
            
            if word in text:
                original_word = word

                print(original_word) #test

                html_word = html_line.format(original_word.strip(marker))

                text = text.replace(original_word, html_word)
                
                if word not in already_exists:
                    already_exists += word
                    words_count += 1

        return words_count, text

    linking_words_count, updated_essay_linking_words = count_and_replace(linking_words, "<span class='jsx-2885589388 linking-words'><div class='jsx-1879403401 root '><span contenteditable='false' class='jsx-1879403401 text'>{}</span><span class='jsx-1879403401'></span></div></span>", essay_linking_words, "#")
    repetitive_words_count, updated_essay_repetitive_words = count_and_replace(repetitive_words, "<span class='jsx-2310580937 repeated-word'><div class='jsx-1879403401 root '><span contenteditable='false' class='jsx-1879403401 text'>{}</span><span class='jsx-1879403401'></span></div></span>", essay_repetitive_words, "^")

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
    
    data = (topic, original_text, paragraphs_count, words_count, grammar_mistakes_count, linking_words_count, repetitive_words_count, submitted_by, band_score, sidebar_comments, current_date, essay_grammar_mistakes, updated_essay_linking_words, updated_essay_repetitive_words, corrected_essay)
    
    return data
