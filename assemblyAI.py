import assemblyai as aai
import os

API_KEY = os.environ.get("ASSEMBLYAI_API_KEY")

aai.settings.api_key = API_KEY

FILE_URL = "audio.mp3"

def run():
    config = aai.TranscriptionConfig(speaker_labels=True)

    transcriber = aai.Transcriber()

    transcript = transcriber.transcribe(
        FILE_URL,
        config=config   
    )

    result = ""
    for utterance in transcript.utterances:
        result+= (f"\nSpeaker: {utterance.speaker}: {utterance.text}\n")

    return result