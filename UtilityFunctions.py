
from tqdm import tqdm
from gtts import gTTS
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip
import Levenshtein as lev
import cv2
from PIL import Image
import os

# Function to add subtitle to frame
def add_subtitle_to_frame(frame, subtitle):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_color = (255, 255, 255)  # White color
    font_thickness = 1
    margin = 10  # Margin from the bottom
    line_height = 20  # Height of each line of text

    # Split subtitle into multiple lines if needed
    lines = [subtitle[i:i+40] for i in range(0, len(subtitle), 40)]  # Split at max 40 characters per line

    # Add each line of text to the frame
    y = frame.shape[0] - margin - line_height * len(lines)
    for line in lines:
        (text_width, text_height), baseline = cv2.getTextSize(line, font, font_scale, font_thickness)
        x = (frame.shape[1] - text_width) // 2
        cv2.putText(frame, line, (x, y), font, font_scale, font_color, font_thickness)
        y += line_height

    return frame

# Split video into frames
def extract_frames(video_path, frames_folder):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return 0
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_path = os.path.join(frames_folder, f'frame_{count:04d}.jpg')
        cv2.imwrite(frame_path, frame)
        count += 1
    cap.release()
    print(f'Extracted {count} frames from the video.')
    return count

# Colorize frames and generate captions
def colorize_frames_and_generate_captions(frames_folder, colorized_folder, frame_count, caption_interval=72):
    frame_files = sorted(os.listdir(frames_folder))
    captions = {}

    for idx, frame_file in tqdm(enumerate(frame_files), total=frame_count, desc="Colorizing frames and generating captions"):
        frame_path = os.path.join(frames_folder, frame_file)
        colorized_frame = colorizer.get_transformed_image(path=frame_path, render_factor=35, watermarked=False)
        colorized_frame_path = os.path.join(colorized_folder, frame_file)
        colorized_frame.save(colorized_frame_path)

        if idx % caption_interval == 0:
            # Generate caption
            colorized_frame_pil = Image.open(colorized_frame_path).convert("RGB")
            caption = captioner(colorized_frame_pil)[0]['generated_text']
            captions[frame_file] = caption
            print(f"Frame {frame_file}: {caption}")

    print('Colorized all frames and generated captions.')
    return captions

# Add captions to frames
def add_captions_to_frames(frames_folder, captions, duration=72):
    frame_files = sorted(os.listdir(frames_folder))

    # Initialize variables to keep track of subtitle visibility
    current_caption = None
    subtitle_counter = 0

    for frame_file in tqdm(frame_files, desc="Adding captions as subtitles to frames"):
        frame_path = os.path.join(frames_folder, frame_file)
        frame = cv2.imread(frame_path)

        # If it's time to change the subtitle or the first frame, update the current caption
        if subtitle_counter == 0 or current_caption is None:
            current_caption = captions.get(frame_file, "")

        # Add the subtitle to the frame
        frame_with_caption = add_subtitle_to_frame(frame, current_caption)
        cv2.imwrite(frame_path, frame_with_caption)

        # Increment the subtitle counter
        subtitle_counter = (subtitle_counter + 1) % duration

# Combine frames into video
def create_video_from_frames(frames_folder, output_video_path, frame_count, fps=24):
    frame_files = sorted(os.listdir(frames_folder))
    frame_path = os.path.join(frames_folder, frame_files[0])
    frame = cv2.imread(frame_path)
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    for frame_file in tqdm(frame_files, total=frame_count, desc="Creating video from frames"):
        frame_path = os.path.join(frames_folder, frame_file)
        frame = cv2.imread(frame_path)
        video.write(frame)

    video.release()
    print(f'Created video from frames: {output_video_path}')

# Function to convert text to audio and ensure minimum duration
def text_to_audio(text, output_file, previous_caption="", min_duration=3, max_duration=3, language='en'):
    # Check if the output file already exists
    if os.path.exists(output_file):
        # Load the existing audio file
        existing_audio = AudioSegment.from_mp3(output_file)
        # Calculate the duration of the existing audio
        existing_duration = len(existing_audio) / 1000  # Convert milliseconds to seconds
    else:
        existing_duration = 0

    # Create a gTTS object
    tts = gTTS(text=text, lang=language, slow=False)

    # Save the audio to a temporary file
    temp_file = "temp.mp3"
    tts.save(temp_file)

    # Read the temporary audio file
    audio = AudioSegment.from_mp3(temp_file)

    # Calculate the duration of the audio
    audio_duration = len(audio) / 1000  # Convert milliseconds to seconds

    # Calculate the similarity between the current caption and the previous one
    similarity = lev.ratio(text.lower(), previous_caption.lower()) if previous_caption else 0

    # Check if the current caption is similar to the previous one
    if similarity > 0.8:
        # Add silence to the existing audio if the caption is similar to the previous one
        audio = AudioSegment.silent(duration=(min_duration - existing_duration) * 1000)
    elif audio_duration < min_duration:
        # Pad the audio with silence to reach min_duration
        silence_duration = (min_duration - audio_duration) * 1000  # Convert seconds to milliseconds
        silence = AudioSegment.silent(duration=silence_duration)
        audio = audio + silence
    elif audio_duration > max_duration:
        # Truncate the audio to max_duration
        audio = audio[:max_duration * 1000]  # Convert seconds to milliseconds

    # Save the adjusted audio to the output file
    audio.export(output_file, format="mp3")

    # Delete the temporary file
    os.remove(temp_file)

# Convert captions to audio files
def captions_to_audio(captions, output_folder, interval=3):
    os.makedirs(output_folder, exist_ok=True)

    previous_caption = ""
    for idx, (frame_file, caption) in enumerate(captions.items()):
        audio_file = os.path.join(output_folder, f'audio_{idx:04d}.mp3')
        text_to_audio(caption, audio_file, previous_caption=previous_caption, min_duration=interval, max_duration=interval)
        previous_caption = caption

    print(f"Converted {len(captions)} captions to audio.")

# Concatenate audio files
def concatenate_audio_files(input_folder, output_file):
    audio_files = sorted(os.listdir(input_folder))
    combined_audio = None

    for audio_file in audio_files:
        audio_path = os.path.join(input_folder, audio_file)
        audio_segment = AudioSegment.from_mp3(audio_path)
        if combined_audio is None:
            combined_audio = audio_segment
        else:
            combined_audio += audio_segment

    combined_audio.export(output_file, format="mp3")
    print(f"Concatenated {len(audio_files)} audio files into {output_file}.")

# Merge audio with video
def merge_audio_with_video(video_file, audio_file, output_file):
    video = VideoFileClip(video_file)
    audio = AudioFileClip(audio_file)
    video = video.set_audio(audio)
    video.write_videofile(output_file, codec="libx264", audio_codec="aac")
    print(f"Merged audio with video: {output_file}")

# Function to colorize video
def colorize_video(colorizer, captioner, video_path, output_path='.', output_name='output', fps=24, interval=3):
    output_frames_path = f'{output_path}/frames'
    colorized_frames_path = f'{output_path}/colorized_frames'
    video_without_audio_path = f'{output_path}/output_video_without_audio.mp4'

    os.makedirs(output_frames_path, exist_ok=True)
    os.makedirs(colorized_frames_path, exist_ok=True)



    # Execute the steps
    frame_count = extract_frames(video_path, output_frames_path)
    captions = colorize_frames_and_generate_captions(output_frames_path, colorized_frames_path, frame_count, caption_interval=interval*fps)
    add_captions_to_frames(colorized_frames_path, captions, duration=interval*fps)
    create_video_from_frames(colorized_frames_path, video_without_audio_path, frame_count, fps=fps)

    print('Video colorization, captioning, and subtitle addition completed!')

    # Execute the steps
    output_folder = f'{output_path}/captions_audio'
    output_audio_file = f'{output_path}/audio_combined.mp3'
    output_video_with_audio = f'{output_path}/{output_name}.mp4'

    captions_to_audio(captions, output_folder, interval=interval)
    concatenate_audio_files(output_folder, output_audio_file)
    merge_audio_with_video(video_without_audio_path, output_audio_file, output_video_with_audio)

    print('Audio generation and merging with video completed!')

    # Define the directories to be removed
    dirs_to_remove = [output_frames_path, colorized_frames_path, output_folder]

    # Remove the directories
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"Removed directory: {dir_path}")
        else:
            print(f"Directory does not exist: {dir_path}")
