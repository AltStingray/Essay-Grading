import assemblyai as aai

aai.settings.api_key = "bc90a68cad05489689f948691bc5d3de"

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