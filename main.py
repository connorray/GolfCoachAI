from IPython.display import display, Image, Audio

import cv2
import base64
import time
import openai
import os
import requests
import numpy as np
import pygame

# Initialize pygame mixer
pygame.mixer.init()

os.environ["OPENAI_API_KEY"] = "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"
video = cv2.VideoCapture("data/golf-swing.mp4")

base64Frames = []
while video.isOpened():
    success, frame = video.read()
    if not success:
        break
    _, buffer = cv2.imencode(".jpg", frame)
    base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

video.release()
print(len(base64Frames), "frames read.")

# Initialize the display with the first frame or a placeholder image
if base64Frames:
    display_handle = display(
        Image(data=base64.b64decode(base64Frames[0].encode("utf-8"))), display_id=True
    )
    time.sleep(0.025)
else:
    # Handle the case where no frames were read
    print("No frames to display.")
    display_handle = None

# Update the display with the rest of the frames
if display_handle is not None:
    for img in base64Frames[1:]:  # Skip the first frame since it's already displayed
        display_handle.update(Image(data=base64.b64decode(img.encode("utf-8"))))
        time.sleep(0.025)

# Assuming you have your base64 string in base64Frames
for base64_str in base64Frames:
    # Decode the base64 string to bytes
    img_bytes = base64.b64decode(base64_str)

    # Convert the bytes to a numpy array
    nparr = np.frombuffer(img_bytes, np.uint8)

    # Read the image from the numpy array
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Display the image
    cv2.imshow("Frame", img)

    # Wait for 25ms and check if the user wants to exit
    if cv2.waitKey(25) & 0xFF == ord("q"):
        break

# Release the window
cv2.destroyAllWindows()

PROMPT_MESSAGES = [
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
    "messages": PROMPT_MESSAGES,
    "api_key": os.environ["OPENAI_API_KEY"],
    "headers": {"Openai-Version": "2020-11-07"},
    "max_tokens": 500,
}

result = openai.ChatCompletion.create(**params)
print(result.choices[0].message.content)

response = requests.post(
    "https://api.openai.com/v1/audio/speech",
    headers={
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
    },
    json={
        "model": "tts-1",
        "input": result.choices[0].message.content,
        "voice": "onyx",
    },
)

audio = b""
for chunk in response.iter_content(chunk_size=1024 * 1024):
    audio += chunk
Audio(audio, autoplay=True)

# save the audio to file
with open("output_audio.mp3", "wb") as audio_file:
    audio_file.write(audio)
# Load the audio file and play it
pygame.mixer.music.load("output_audio.mp3")
pygame.mixer.music.play()

# Wait for the music to play before exiting
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)
