import os
import cv2
import numpy as np
import random
import logging
from kafka import KafkaConsumer
from moviepy.editor import VideoFileClip, AudioFileClip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Kafka consumer
def create_consumer(anime_name):
    topic_name = f'anime_{anime_name}'
    return KafkaConsumer(
        topic_name,
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group',
        consumer_timeout_ms=30000,
        value_deserializer=lambda x: x
    )

def add_blend_transition(image1, image2, duration=2):
    height, width, _ = image1.shape
    blend_frames = int(duration * 5)
    for i in range(blend_frames):
        alpha = i / blend_frames
        blended_image = cv2.addWeighted(image1, 1 - alpha, image2, alpha, 0)
        yield blended_image

def add_crossfade(image1, image2, duration=2):
    fade_frames = int(duration * 5)
    for alpha in range(fade_frames):
        alpha_value = int(255 * (alpha / fade_frames))
        blended_image = cv2.addWeighted(image1, 1 - (alpha_value / 255), image2, alpha_value / 255, 0)
        yield blended_image

def add_random_shade(image, probability=0.5):
    if random.random() < probability:
        shade_value = random.randint(50, 150)
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv_image[:, :, 2] = np.clip(hsv_image[:, :, 2] + shade_value, 0, 255)
        shaded_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
        return shaded_image
    else:
        return image

def add_gaussian_blur(image, probability=0.5):
    if random.random() < probability:
        kernel_size = random.choice([3, 5, 7])
        blurred_image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        return blurred_image
    else:
        return image

def create_video_from_images(images, output_video_path, fps=10):
    if not images:
        logger.warning("No images to create video.")
        return

    first_image = images[0]
    height, width, _ = first_image.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    prev_frame = None

    for i, frame in enumerate(images):
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))
        
        frame = add_random_shade(frame)
        frame = add_gaussian_blur(frame)

        if prev_frame is not None:
            transition = random.choice([add_crossfade, add_blend_transition])
            transition_frames = transition(prev_frame, frame)
            for transition_frame in transition_frames:
                video.write(transition_frame)
        else:
            video.write(frame)

        prev_frame = frame
        logger.info(f"Processed frame {i+1}/{len(images)}")

    cv2.destroyAllWindows()
    video.release()
    logger.info(f"Video created successfully at {output_video_path}")

def add_audio_to_video(video_path, audio_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    final_clip = video_clip.set_audio(audio_clip)
    final_output_path = video_path.split('.')[0] + '_with_audio.mp4'
    final_clip.write_videofile(final_output_path, codec='libx264', audio_codec='aac')
    logger.info(f"Video with audio created at {final_output_path}")

def consume_images(anime_name, output_video_path, audio_path=None):
    os.makedirs('received_images', exist_ok=True)
    consumer = create_consumer(anime_name)
    images = []
    
    try:
        for message in consumer:
            image_bytes = message.value
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is not None:
                images.append(image)
                image_path = f'received_images/{anime_name}_image_{len(images)}.png'
                #cv2.imwrite(image_path, image)
                logger.info(f"Saved {image_path}")
            else:
                logger.warning('Failed to decode image')

        if images:
            create_video_from_images(images, output_video_path)
            if audio_path:
                add_audio_to_video(output_video_path, audio_path)
        else:
            logger.info('No images received to create a video')

    except Exception as e:
        logger.error(f'Error consuming images: {e}')
    finally:
        consumer.close()

# Usage example
if __name__ == "__main__":
    anime_name = input("Enter the anime name: ")
    output_video_path = f'/home/aditya/reddit-image-scrapper/RedditImageScrapper/{anime_name}_video.mp4'
    audio_path = input("Enter the path to the audio file (or leave empty if no audio): ").strip() or None
    consume_images(anime_name, output_video_path, audio_path)
