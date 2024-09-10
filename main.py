import streamlit as st
import os
import tempfile
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
from pysrt import SubRipFile, SubRipItem, SubRipTime

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Ensure temp directory exists
os.makedirs("temp", exist_ok=True)

# Function to format timestamp
def format_timestamp(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# Function to display timestamped text
def display_timestamped_text(srt_content):
    text = ""
    for item in srt_content:
        start_time = format_timestamp(item.start.seconds)
        end_time = format_timestamp(item.end.seconds)
        text += f"[{start_time} - {end_time}] {item.text}\n\n"
    return text

# Function to save uploaded file temporarily
def save_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    return None

# Function to convert video to audio
def video_to_audio(video_file):
    audio_file = os.path.splitext(video_file)[0] + '.wav'
    command = f"ffmpeg -i \"{video_file}\" -acodec pcm_s16le -ar 16000 \"{audio_file}\" -y"
    subprocess.call(command, shell=True)
    return audio_file

# Function to translate SRT content
def translate_srt(srt_content, target_lang):
    translated_srt = SubRipFile()
    for index, item in enumerate(srt_content):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a very helpful and talented translator who can translate all languages."},
                {"role": "user", "content": f"Translate the following text to {target_lang}. Only provide the translation, no additional comments:\n{item.text}"}
            ]
        )
        translated_text = response.choices[0].message.content.strip()
        translated_item = SubRipItem(index + 1, item.start, item.end, translated_text)
        translated_srt.append(translated_item)
    return translated_srt

# Streamlit app
def main():
    st.set_page_config(page_title="Multi-Language Video Translation App", layout="wide")

    st.title("🎥🌐 Multi-Language Video Translation App")
    st.markdown("""
    Welcome to the Multi-Language Video Translation App! 🚀 This magical tool allows you to:
    1. 📤 Upload a video file
    2. 🌍 Choose multiple languages for translation
    3. 📝 Get transcriptions and translations in SRT format for each selected language
    
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
                    temp_video_path = save_uploaded_file(video_file)

                    # Convert video to audio
                    temp_audio_path = video_to_audio(temp_video_path)

                    # Transcribe audio
                    with open(temp_audio_path, "rb") as audio_file:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="srt"
                        )

                    # Parse the SRT content
                    original_srt = SubRipFile.from_string(transcription)

                    # Display original transcript with timestamps and allow editing
                    st.subheader("📜 Original Transcript")
                    st.text_area("Edit the transcript if needed:", display_timestamped_text(original_srt), height=400, key="original_transcript")

                    # Translate transcription for each selected language
                    for index, lang in enumerate(selected_languages):
                        target_lang = lang.split(' (')[1][:-1]  # Extract English name
                        native_name = lang.split(' (')[0]  # Extract native name

                        with st.spinner(f"Translating to {native_name}... 🌟"):
                            translated_srt = translate_srt(original_srt, target_lang)

                            # Display translated transcript with timestamps
                            st.subheader(f"🌟 {native_name} Translation")
                            st.text_area("", display_timestamped_text(translated_srt), height=400, key=f"translated_text_{index}")

                            # Prepare SRT content for download
                            srt_content = '\n'.join(str(item) for item in translated_srt)

                            # Download button for translated SRT
                            st.download_button(
                                label=f"📥 Download {native_name} SRT",
                                data=srt_content,
                                file_name=f"{target_lang.lower().replace(' ', '_')}.srt",
                                mime="text/srt",
                                key=f"download_button_{index}"
                            )

                    # Clean up temporary files
                    os.unlink(temp_video_path)
                    os.unlink(temp_audio_path)

            except Exception as e:
                st.error(f"🚨 An error occurred: {str(e)}")
                st.error("🔧 Please make sure you have ffmpeg installed and the OpenAI API key is set correctly in your environment variables.")

    st.markdown("""
    ### 🌈 How to use:
    1. 📤 Upload your video file using the file uploader above.
    2. 🌍 Select one or more languages for translation from the dropdown menu.
    3. 🚀 Click the "Process Video" button to start the transcription and translation process.
    4. ⏳ Wait for the processing to complete. This may take a few minutes depending on the video length and the number of languages selected.
    5. 📝 Review and edit the original transcript if needed.
    6. 👀 Review the translations in the text areas provided for each language.
    7. 💾 Download the SRT files for the translated subtitles using the download buttons for each language.

    📢 Note: This app uses advanced AI models for transcription and translation, ensuring high-quality results across a wide range of languages. It's like having a team of polyglot geniuses at your fingertips! 🧠✨
    """)

if __name__ == "__main__":
    main()