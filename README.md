This program web application is developed using Flask and Python programming language.

The program contains the following API functionality: Flask, Dropbox, MoviePy, AssemblyAI, OpenAI, requests, MarkupSafe, Gunicorn, RQ, Redis.

1.Flask - The main web framework used to connect backend logic and frontend HTML+CSS of the applicaton.

2.Dropbox - The cloud storage provider. User will need to authorize into his valid Dropbox account and proceed by clicking on the continue buttons. Then, copy the link of the video from the Dropbox website and pass it to the program. The program will download the video from the link, again using Dropbox API.

3.MoviePy - Python library that allows to convert video files into an audio files, so the transcription and summarization can be accomplished.

4.AssemblyAI - API that provides clear and structured transcription with diarization(speakers separation) option. It takes previously converted audio file and makes a transcription text out of it.

5.OpenAI - API that provides GPT-4o model to analyze the previously generated transcription and to provide a summary report based on the given prompt.

6.requests - Python library to make GET and POST requests to retrieve data.

7.MarkupSafe - A minor addition to prevent SQL injections in input fields.

Program processing algorithm:

By clicking on the "Authorize" button the user will be redirected to the official Dropbox website to complete authorization. No user credentials passed to the program, except an auto collec of the access token after the user successfully logs into account and clicks "Continue".
