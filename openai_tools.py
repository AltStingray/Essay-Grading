from openai import OpenAI
from json import loads
import os
# So, what we will do here is the following:
# We will feed gpd model steps by chunks, and collecting responses one by one. 
# We will append to the original text and replace it by new changes every time.
# After gpt have successfully completed all the steps we will break the loop and make it check the final result one more time
# making adjusments if needed. 
# This will produce a really clean and high quality output.

OPENAI_API_KEY = os.environ.get("N_OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def run_essay_grading(topic, essay_text, submitted_by):

    essay = f"The topic of the essay: {topic}.\nThe essay: {essay_text} \nSubmitted by: {submitted_by}"

    example_results_dict = {
        "paragraphs_count": "paragraphs_count",
        "grammar_mistakes": ["1list1", "2of2", "3words3", "4that4", "5contain5", "6a6", "7mistake7", "8and8", "9wrapped9", "10in10", "11sequence11", "12number12"],
        "corrected_words": ["corrected version of the word 1 (grammar rule 1)", "corrected version of the word 2 (grammar rule 2)", "..."],
        "linking_words": ["#list#", "#of#", "#all#", "#linking#", "#words#"],
        "repetitive_words": ["^list^", "^of^", "^all^", "^repetitive^", "^words^"],
        "unnecessary_words": ["-list-", "-of-", "-all-", "-unnecessary-", "-words-"], 
        "overall_band_score": "overall_band_score(float value)",
    }
    
    introduction = f'''
    Introduction: 
    You are an IETLS teacher and professional grammar checker that provides feedback on candidate's essays. 
    You are given a topic and an essay text based on this topic. 
    Provide the grading based on the IELTS standards. Your primary task is finding grammar mistakes, linking words, repetative words and unnecessary words in the candidate's essay.

    Instruction:
    You will be given multiple steps. In each step you will be given example dictionaries, how each key and it's value should be structured, in which format and how every word should be wrapped.
    Every word/sentence placed in a list should exactly match word/sentence in the essay, either it's lower or upper case, and it should be marked/enclosed properly as well.
    Enclose the dict, all of the keys and values into double quotes, not single.
    Create an empty dictionary with an "update" key in which value you will then store the following results.
    Do not include anything else except the things you are being prompted. No additional commments or notes.
    Do not rush with your answer. Take your time and process each of the following steps sequentially.
    '''

    prompt_1 = '''

    Step 1 - In the provided essay text take at least 30 seconds to identify all of the words that contain grammar mistakes. Then, wrap each word/sentence that contains grammar mistake with the sequence number(i.e. 1example1). So the each next identified grammar mistake increments the sequence number by 1. (Note: If one mistake contains two or more words, enclose them altogether with a single pair of a sequence number(i.e. 2enclose like that2)).
    
    Store the modified essay text as a value into the 'essay_grammar_mistakes' dictionary key.

    Step 2 - Store all of the found grammar mistakes each wrapped in a sequence number into the 'grammar_mistakes' list. Example: "grammar_mistakes": ["1list1", "2of2", "3words3", "4that4", "5contain5", "6a6", "7mistake7", "8and8", "9wrapped9", "10in10", "11sequence11", "12number12"]

    Step 3 - Provide corrected versions of the words containing grammar mistakes as shown in the following example: "corrected_words": ["corrected version of the word 1 (grammar rule 1)", "corrected version of the word 2 (grammar rule 2)", "..."]. You should display the corrected word and next to it in the parentheses () briefly describe the cause of the mistake, like so: "a (Missing an article)", "restricted (Passive form)", "areas (Spelling)", "and (Word choice)", etc.
    
    Include 'essay_grammar_mistakes', 'grammar_mistakes' and 'corrected_words' keys and values inside the 'update' key dictionary.

    Finally, return the 'update' dictionary.
    '''

    #Note: Ingore the sequential numbers in the essay text, as this is your doings from the previous iteration.
    prompt_2 = '''
    Linking words definition: 'Linking words, also known as transition words, are words and phrases like 'however', 'on the other hand', 'besides' or 'in conclusion' that connect clauses, sentences, paragraphs, or other words.'
    
    Step 1 - In the given essay text identify all of the linking words throughout the whole text, then wrap all of them with the '#' mark. (Note: If linking word contains punctuation sign, just separate them with one whitespace and wrap the linking word with '#').

    Store the modified essay text as a value into the 'essay_linking_words' dictionary key.

    Save the modified essay text as a value into the 'modified_text' key.

    Step 2 - Store all of the found linking words into the 'linking_words' list wrapped with the '#', as following: "linking_words": ["#list#", "#of#", "#all#", "#linking#", "#words#"].
    
    Include the 'linking_words' and 'essay_linking_words' keys and values inside the 'update' key dictionary.

    Finally, return the 'update' dictionary.
    '''

    #Repetitive words, are the words in a candidate's text which get repeated more than 4 times per text. For example, if the word 'people', "like", "well" or "obviously" appears in text more than 4 times, it is considered a repetitive word and should be marked with '^''
    #Note: Ingore the sequential numbers and '#' marks in the essay text, as those are your doings from the previous iteration.
    prompt_3 = '''
    Repetitive words definition: 'The repetitive use of the same word in a text is called "redundancy" or "word repetition." It can make the text less engaging and may indicate a need for variety or synonyms to improve readability and flow. Note: Syncategorematic words are not repetitive words. Examples of syncategorematic terms include: articles (for example, 'the' and 'a') connectives (for example, 'and' and 'or') prepositions (for exmaple, 'in' and 'at') quantifiers (for example, 'some' and 'all').

    Step 1 - In the given essay text identify all of the repetitive words throughout the whole text, even if they have already been identified, and wrap them with the '^' mark. 

    Store the modified essay text as a value into the 'essay_repetitive_words' dictionary key.

    Step 2 - Store all of the found repetitive words into the 'repetitive_words' list wrapped with the '^', as shown in the following example: "repetitive_words": ["^list^", "^of^", "^all^", "^repetitive^", "^words^"]. 
    
    Include the 'repetitive_words' and 'essay_repetitive_words' keys and values inside the 'update' key dictionary.

    Finally, return the 'update' dictionary.
    '''

    #Note: Ingore the sequential numbers, '#' and '^' marks in the essay text, as those are your doings from the previous iteration.
    prompt_4 = '''
    Unnecessary words defininion: 
    'Four types of unnecessary words and phrases to avoid for conciseness: 

    Dummy Subjects: Avoid words like "there is/are" and "it is/was" that add no meaning. 
    Example: "There are great skiing resorts in Colorado." to "Colorado has great skiing resorts." 

    Nominalizations: Use verbs instead of nouns made from verbs (e.g., "decision" vs. "decide"). 
    Example: "The conjugation of verbs is difficult." to "Conjugating verbs is difficult." 
    
    Infinitive Phrases: Replace "to + verb" phrases with direct verbs. 
    Example: "Our duty was to clean and to wash." to "We cleaned and washed." 
    Circumlocutions: Avoid lengthy phrases that can be said in fewer words. 
    Example: "Owing to the fact that..." to "Since..." In short, aim for direct, simplified wording by cutting out filler expressions.'

    Step 1 - In the given essay text identify all of the possible unnecessary words that you would get rid of to increase the overall clarity and make the essay better, and wrap them with the '-' mark. 

    Store the modified essay text as a value into the 'essay_unnecessary_words' dictionary key.

    Step 2 - Store all of the found unnecessary words into the 'unnecessary_words' list wrapped with the '-', as shown in the following example: "unnecessary_words": ["-list-", "-of-", "-all-", "-unnecessary-", "-words-"]. 

    Include the 'unnecessary_words' and 'essay_unnecessary_words' keys and values inside the 'update' key dictionary.

    Finally, return the 'update' dictionary.
    '''

    band_score = '''
    Step 1 - Evaluate the given candidate's essay text based on the IELTS standarts and return the corrected version of it. Store the result as a value in the "corrected_essay" key.

    Step 2 - Estimate the Overall Band Score for the given essay and store it into the "overall_band_score" key as a float value as shown in the following example: "overall_band_score": "overall_band_score(float value)".

    Step 3 - Provide the number of paragraphs in the the essay and store this value into the "paragraphs_count" key.

    Include the 'corrected_essay', 'overall_band_score' and 'paragraphs_count' keys and values inside the 'update' key dictionary.

    Finally, return the 'update' dictionary.
    '''

    final_prompt = '''
    You are a helpful assistant. You are specialized in essay grading.
    In the given dictionary you can see different sections. One of them is modified essay text in 'original_text'. 
    Previously you made some gradings and added all of those sections. Your final task is to review the 'original_text' and other sections for the last time
    and to make some appropriate adjustments. Make sure that each enclosed word in 'original_text' corresponds to the relevant section.
    Make sure that grammar, linking, repetitive and unnecessary words are apropriate and correct.
    Return the adjusted dictionary.
    '''

    prompts = [prompt_1, prompt_2, prompt_3, prompt_4, band_score]

    final_dict = {
        "original_topic": topic,
        "original_text": essay_text,
        "submitted_by": submitted_by,
    }

    for prompt in prompts:

        messages = [
            {"role": "system", "content": introduction},
            {"role": "user", "content": essay},
            {"role": "user", "content": prompt}
        ]

        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=messages,
            max_tokens=16000,
            )
        
        result = response.choices[0].message.content

        print(f"\nResult before strip:\n\n{result}")

        strip_response = strip_text(result)
        print(f"\nResult after strip:\n\n{strip_response}")
        if strip_response.startswith("{"):
            response = strip_response
        else:
            response = loads('{"' + strip_response + '"}')

        print(f"\nResult after json load: {response}")

        final_dict.update(response["update"])

    print(f"Final dictionary: {final_dict}") # test

    return final_dict


def run_summary_report(prompt, content):

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f'''{content}'''}],
        max_tokens=16000,
        )
    
    response = response.choices[0].message.content

    return response

def strip_text(text):

    if text.startswith("```python"):
        stripped_text = text.strip("```pyton")
    elif text.startswith("```json"):
        stripped_text = text.strip("```json")
    else:
        stripped_text = text.strip("```")
    
    return stripped_text