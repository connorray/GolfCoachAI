import cv2
import base64
import openai
import os
import requests
import streamlit as st
import tempfile
from IPython.display import Audio
import pygame
import imageio
import threading

# Initialize pygame mixer
pygame.mixer.init()

os.environ["OPENAI_API_KEY"] = "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"


# Function to convert video to GIF
def convert_video_to_gif(video_path, gif_path):
    cap = cv2.VideoCapture(video_path)
    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame)

    cap.release()
    imageio.mimsave(gif_path, frames, fps=10)


def process_video(video_file):
    print(video_file)
    video = cv2.VideoCapture(video_file)

    base64Frames = []
    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

    video.release()
    print(len(base64Frames), "frames read.")

    if base64Frames:
        # Create the prompt messages with the selected frames
        prompt_messages = [
            {
                "role": "user",
                "content": [
                    "These are frames from a video of my golf swing that I want to receive golf swing coaching on. Create a short voiceover script in the style of a PGA golf coach on how I can improve my golf swing. Only include the narration.",
                    *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::20]),
                ],
            },
        ]
        params = {
            "model": "gpt-4-vision-preview",
            "messages": prompt_messages,
            "api_key": os.environ["OPENAI_API_KEY"],
            "headers": {"Openai-Version": "2020-11-07"},
            "max_tokens": 500,
        }

        # Call the OpenAI API
        result = openai.ChatCompletion.create(**params)
        script = result.choices[0].message.content
        print(script)

        # Generate audio from the script
        response = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            },
            json={
                "model": "tts-1",
                "input": script,
                "voice": "onyx",
            },
        )

        return response

    else:
        st.error("No frames to display, cannot process the video.")
        return None


st.title("Golf Swing Feedback")

uploaded_file = st.file_uploader("Choose a video...", type=["mp4", "mov", "avi", "mkv"])
if st.button("Get Feedback"):
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmpfile:
            tmpfile.write(uploaded_file.read())
            video_path = tmpfile.name

        if video_path:
            try:
                with st.spinner("Processing..."):
                    # Convert video to GIF
                    gif_path = video_path.replace(".mp4", ".gif")
                    convert_video_to_gif(video_path, gif_path)

                    # Process video and play audio as before
                    response = process_video(video_path)
                    audio = b""
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        audio += chunk

                    with open("output_audio.mp3", "wb") as audio_file:
                        audio_file.write(audio)

                    pygame.mixer.music.load("output_audio.mp3")
                    pygame.mixer.music.play()

                    # Display GIF in Streamlit
                    st.image(gif_path)

                    # Wait for the audio to finish
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)

            finally:
                os.remove(video_path)
                if os.path.exists(gif_path):
                    os.remove(gif_path)
        else:
            st.warning("Please upload a valid video first.")
