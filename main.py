import os
import openai
import requests
from telegram import Voice, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
import av
from dotenv import load_dotenv

load_dotenv()

# Replace with your actual OpenAI API key and Telegram token
OPENAI_API_KEY = "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"
TELEGRAM_TOKEN = "6227413852:AAFb8O-vLFQ8l38qM-TtuA8HD9e-1rmcwFc"

openai.api_key = OPENAI_API_KEY

def convert_ogg_to_mp3(input_path, output_path):
    input_container = av.open(input_path)
    output_container = av.open(output_path, mode="w")

    input_stream = input_container.streams.audio[0]
    output_stream = output_container.add_stream("mp3", rate=input_stream.rate)

    for frame in input_container.decode(input_stream):
        for packet in output_stream.encode(frame):
            output_container.mux(packet)

    # Flush remaining packets
    for packet in output_stream.encode(None):
        output_container.mux(packet)

    input_container.close()
    output_container.close()

def summarize_text(text):
    prompt = f"Organiza las ideas y resume el siguiente texto en bullet points::\n\n{text}\n\nResumen:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=400,
        n=1,
        stop=None,
        temperature=0.5,
    )

    summary = response.choices[0].text.strip()
    return summary

def process_voice_note(voice_note_url):
    response = requests.get(voice_note_url)

    with open("temp_voice_note.ogg", "wb") as f:
        f.write(response.content)

    convert_ogg_to_mp3("temp_voice_note.ogg", "temp_voice_note.mp3")

    with open("temp_voice_note.mp3", "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)

    summary = summarize_text(transcript["text"])

    os.remove("temp_voice_note.ogg")
    os.remove("temp_voice_note.mp3")

    return summary

def voice_note_handler(update: Update, context: CallbackContext):
    voice_note = update.message.voice
    voice_note_url = context.bot.get_file(voice_note.file_id).file_path

    bullet_points = process_voice_note(voice_note_url)

    context.bot.send_message(chat_id=update.effective_chat.id, text=bullet_points)

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.voice, voice_note_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
