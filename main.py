import streamlit as st
import os
import subprocess
import whisper
import openai
from pysrt import SubRipFile, SubRipItem, SubRipTime
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
    return result["segments"]

# Function to create SRT file
def create_srt(segments, filename):
    srt = SubRipFile()
    for i, segment in enumerate(segments):
        start = SubRipTime(seconds=segment['start'])
        end = SubRipTime(seconds=segment['end'])
        text = segment['text']
        item = SubRipItem(i+1, start=start, end=end, text=text)
        srt.append(item)
    srt.save(filename)

# Function to translate text using GPT-4
def translate_text(text, target_lang):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are a very helpful and talented translator who can translate any text to any language. You know every language like it is your native language. Your job is to translate the given text to {target_lang}. Please do not translate it word by word, but rather focus on conveying the meaning of the text in a way that is natural and fluent for a native speaker of the target language."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

# Streamlit app
def main():
    st.set_page_config(page_title="Video Translation App", layout="wide")

    st.title("🎥🌐 Video Translation App")
    st.markdown("""
    Welcome to the Video Translation App! 🚀 This magical tool allows you to:
    1. 📤 Upload a video file
    2. 🌍 Choose languages for translation
    3. 📝 Get transcriptions and translations in SRT format
    
    Simply follow the steps below to get started! Let's make your video go global! 🌎🌍🌏
    """)

    # File uploader
    video_file = st.file_uploader("📁 Upload your video file", type=['mp4', 'avi', 'mov'])

    # Extended language selection with native names
    languages = [
        'English (English)', 'Türkçe (Turkish)', 'Español (Spanish)', 'Français (French)', 
        'Deutsch (German)', 'Italiano (Italian)', 'Português (Portuguese)', 'Русский (Russian)', 
        '日本語 (Japanese)', '简体中文 (Chinese Simplified)', '繁體中文 (Chinese Traditional)', 
        '한국어 (Korean)', 'العربية (Arabic)', 'हिन्दी (Hindi)', 'বাংলা (Bengali)', 'اردو (Urdu)', 
        'Bahasa Indonesia (Indonesian)', 'Tiếng Việt (Vietnamese)', 'ไทย (Thai)', 'Nederlands (Dutch)', 
        'Ελληνικά (Greek)', 'Svenska (Swedish)', 'Norsk (Norwegian)', 'Dansk (Danish)', 'Suomi (Finnish)', 
        'Polski (Polish)', 'Українська (Ukrainian)', 'Čeština (Czech)', 'Română (Romanian)', 
        'Magyar (Hungarian)', 'Български (Bulgarian)', 'עברית (Hebrew)', 'Kiswahili (Swahili)', 
        'Bahasa Melayu (Malay)', 'Filipino (Filipino)', 'فارسی (Persian)', 'தமிழ் (Tamil)', 
        'తెలుగు (Telugu)', 'ಕನ್ನಡ (Kannada)', 'മലയാളം (Malayalam)', 'मराठी (Marathi)', 
        'ગુજરાતી (Gujarati)', 'ਪੰਜਾਬੀ (Punjabi)'
    ]
    selected_languages = st.multiselect("🗣️ Select languages for translation", languages)

    if video_file and selected_languages:
        if st.button("🚀 Process Video"):
            try:
                with st.spinner("🔧 Processing video... Please wait, magic takes time! ✨"):
                    # Save uploaded file
                    video_path = os.path.join("temp", video_file.name)
                    with open(video_path, "wb") as f:
                        f.write(video_file.getbuffer())

                    # Convert video to audio
                    audio_file = video_to_audio(video_path)

                    # Transcribe audio
                    segments = transcribe_audio(audio_file)

                    # Create original SRT file
                    original_srt = os.path.join("temp", "original.srt")
                    create_srt(segments, original_srt)

                    # Display original transcript
                    st.subheader("📜 Original Transcript")
                    full_transcript = " ".join([segment['text'] for segment in segments])
                    st.text_area("", full_transcript, height=200)

                    # Translate and create SRT for each selected language
                    for lang in selected_languages:
                        native_name = lang.split(' (')[0]
                        english_name = lang.split(' (')[1][:-1]  # Remove the closing parenthesis
                        translated_segments = []
                        for segment in segments:
                            translated_text = translate_text(segment['text'], english_name)
                            translated_segments.append({
                                'start': segment['start'],
                                'end': segment['end'],
                                'text': translated_text
                            })
                        translated_srt = os.path.join("temp", f"{english_name.lower().replace(' ', '_')}.srt")
                        create_srt(translated_segments, translated_srt)

                        # Display translated transcript
                        st.subheader(f"🌟 {native_name} Translation")
                        full_translated_text = " ".join([segment['text'] for segment in translated_segments])
                        st.text_area("", full_translated_text, height=200)

                        # Download button for translated SRT
                        with open(translated_srt, "rb") as file:
                            st.download_button(
                                label=f"📥 Download {native_name} SRT",
                                data=file,
                                file_name=f"{english_name.lower().replace(' ', '_')}.srt",
                                mime="text/srt"
                            )

                    # Clean up temporary files
                    os.remove(video_path)
                    os.remove(audio_file)
                    os.remove(original_srt)
                    for lang in selected_languages:
                        english_name = lang.split(' (')[1][:-1]
                        os.remove(os.path.join("temp", f"{english_name.lower().replace(' ', '_')}.srt"))

            except Exception as e:
                st.error(f"🚨 An error occurred: {str(e)}")
                st.error("🔧 Please make sure you have ffmpeg installed and the OpenAI API key is correct.")

    st.markdown("""
    ### 🌈 How to use:
    1. 📤 Upload your video file using the file uploader above.
    2. 🌍 Select one or more languages for translation from the dropdown menu.
    3. 🚀 Click the "Process Video" button to start the translation process.
    4. ⏳ Wait for the processing to complete. This may take a few minutes depending on the video length.
    5. 👀 Review the original transcript and translations in the text areas provided.
    6. 💾 Download the SRT files for each language using the download buttons.

    📢 Note: This app uses advanced AI models (OpenAI's GPT-4) for transcription and translation, ensuring high-quality results across a wide range of languages. It's like having a polyglot genius at your fingertips! 🧠✨
    """)

if __name__ == "__main__":
    main()