import streamlit as st
import os
import subprocess
import whisper
import openai
from pysrt import SubRipFile, SubRipItem
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Ensure temp directory exists
os.makedirs("temp", exist_ok=True)

# Function to convert video to audio
def video_to_audio(video_file):
    audio_file = os.path.splitext(video_file)[0] + '.wav'
    command = f"ffmpeg -i \"{video_file}\" -acodec pcm_s16le -ar 16000 \"{audio_file}\""
    subprocess.call(command, shell=True)
    return audio_file

# Function to transcribe audio using Whisper
def transcribe_audio(audio_file):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result["text"]

# Function to create SRT file
def create_srt(transcript, filename):
    srt = SubRipFile()
    lines = transcript.split('. ')
    for i, line in enumerate(lines):
        item = SubRipItem(i+1, start=i*5, end=(i+1)*5, text=line)
        srt.append(item)
    srt.save(filename)

# Function to translate text using GPT-4
def translate_text(text, target_lang):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are a very helpful and talented translator who can translate all languages and srt files. Translate the following text to {target_lang}."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

# Streamlit app
def main():
    st.set_page_config(page_title="Video Translation App", layout="wide")

    st.title("🎥🌐 Video Translation App")
    st.markdown("""
    Welcome to the Video Translation App! This tool allows you to:
    1. Upload a video file
    2. Choose languages for translation
    3. Get transcriptions and translations in SRT format
    
    Simply follow the steps below to get started!
    """)

    # File uploader
    video_file = st.file_uploader("Upload your video file", type=['mp4', 'avi', 'mov'])

    # Extended language selection
    languages = [
        'English', 'Turkish', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Russian', 'Japanese', 
        'Chinese (Simplified)', 'Chinese (Traditional)', 'Korean', 'Arabic', 'Hindi', 'Bengali', 'Urdu', 
        'Indonesian', 'Vietnamese', 'Thai', 'Dutch', 'Greek', 'Swedish', 'Norwegian', 'Danish', 'Finnish', 
        'Polish', 'Ukrainian', 'Czech', 'Romanian', 'Hungarian', 'Bulgarian', 'Hebrew', 'Swahili', 'Malay',
        'Filipino', 'Persian', 'Tamil', 'Telugu', 'Kannada', 'Malayalam', 'Marathi', 'Gujarati', 'Punjabi'
    ]
    selected_languages = st.multiselect("Select languages for translation", languages)

    if video_file and selected_languages:
        if st.button("Process Video"):
            try:
                with st.spinner("Processing video..."):
                    # Save uploaded file
                    video_path = os.path.join("temp", video_file.name)
                    with open(video_path, "wb") as f:
                        f.write(video_file.getbuffer())

                    # Convert video to audio
                    audio_file = video_to_audio(video_path)

                    # Transcribe audio
                    transcript = transcribe_audio(audio_file)

                    # Create original SRT file
                    original_srt = os.path.join("temp", "original.srt")
                    create_srt(transcript, original_srt)

                    # Display original transcript
                    st.subheader("Original Transcript")
                    st.text_area("", transcript, height=200)

                    # Translate and create SRT for each selected language
                    for lang in selected_languages:
                        translated_text = translate_text(transcript, lang)
                        translated_srt = os.path.join("temp", f"{lang.lower().replace(' ', '_')}.srt")
                        create_srt(translated_text, translated_srt)

                        # Display translated transcript
                        st.subheader(f"{lang} Translation")
                        st.text_area("", translated_text, height=200)

                        # Download button for translated SRT
                        with open(translated_srt, "rb") as file:
                            st.download_button(
                                label=f"Download {lang} SRT",
                                data=file,
                                file_name=f"{lang.lower().replace(' ', '_')}.srt",
                                mime="text/srt"
                            )

                    # Clean up temporary files
                    os.remove(video_path)
                    os.remove(audio_file)
                    os.remove(original_srt)
                    for lang in selected_languages:
                        os.remove(os.path.join("temp", f"{lang.lower().replace(' ', '_')}.srt"))

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.error("Please make sure you have ffmpeg installed and the OpenAI API key is correct.")

    st.markdown("""
    ### How to use:
    1. Upload your video file using the file uploader above.
    2. Select one or more languages for translation from the dropdown menu.
    3. Click the "Process Video" button to start the translation process.
    4. Wait for the processing to complete. This may take a few minutes depending on the video length.
    5. Review the original transcript and translations in the text areas provided.
    6. Download the SRT files for each language using the download buttons.

    Note: This app uses advanced AI models (OpenAI's GPT-4) for transcription and translation, ensuring high-quality results across a wide range of languages.
    """)

if __name__ == "__main__":
    main()