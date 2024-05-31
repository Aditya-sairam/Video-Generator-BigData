import cv2
import os
import random
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

def add_blend_transition(image1, image2, duration=2):
    height, width, _ = image1.shape
    blend_frames = int(duration * 5)  # Total number of blend frames
    for i in range(blend_frames):
        alpha = i / blend_frames  # Alpha value for blending images
        blended_image = cv2.addWeighted(image1, 1 - alpha, image2, alpha, 0)
        yield blended_image


def add_crossfade(image1, image2, duration=2):
    fade_frames = int(duration * 5)  # Total number of fade frames
    for alpha in range(fade_frames):
        alpha_value = int(255 * (alpha / fade_frames))
        blended_image = cv2.addWeighted(image1, 1 - (alpha_value / 255), image2, alpha_value / 255, 0)
        yield blended_image


def add_random_shade(image, probability=0.5):
    if random.random() < probability:
        shade_value = random.randint(50, 150)  # Random shade value between 50 and 150
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv_image[:, :, 2] = np.clip(hsv_image[:, :, 2] + shade_value, 0, 255)
        shaded_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
        return shaded_image
    else:
        return image
    
def add_gaussian_blur(image, probability=0.5):
    if random.random() < probability:
        kernel_size = random.choice([3, 5, 7])  # Random kernel size for blur
        blurred_image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        return blurred_image
    else:
        return image

def create_video_from_images(image_folder, output_video_path, audio_path=None, fps=10):
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]

    # Read the first image to get dimensions
    first_image = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, _ = first_image.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # For MP4 format
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    prev_frame = None  # Keep track of previous frame for transition effect

    for i, image_name in enumerate(sorted(images)):  # Sort images to maintain order
        image_path = os.path.join(image_folder, image_name)
        frame = cv2.imread(image_path)
        # Resize frame if dimensions are different
        if frame.shape[0] != height or frame.shape[1] != width:
            frame = cv2.resize(frame, (width, height))

        frame = add_random_shade(frame)
        frame = add_gaussian_blur(frame)

        if prev_frame is not None:
            # Randomly select transition effect
            transition = random.choice([add_crossfade, add_blend_transition])
            # Apply transition effect
            transition_frames = transition(prev_frame, frame)
            for transition_frame in transition_frames:
                video.write(transition_frame)
        else:
            video.write(frame)

        prev_frame = frame

    cv2.destroyAllWindows()
    video.release()

    if audio_path:
        add_audio_to_video(output_video_path, audio_path)

def add_audio_to_video(video_path, audio_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile(video_path.split('.')[0] + '_with_audio.mp4', codec='libx264', audio_codec='aac')

# Usage example
image_folder = 'C:/Users/adity/OneDrive/Desktop/RedditImageScrapper/RedditImageScraper-main/images'
output_video_path = 'output_video.mp4'
audio_path = 'C:/Users/adity/Downloads/waydown.mp3'  # Update with your audio file path
create_video_from_images(image_folder, output_video_path, audio_path)
