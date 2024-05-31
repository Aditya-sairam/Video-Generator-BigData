import os
import SubDownload
import S3Upload
#import S3ToKafka
#import KafkaConsumer

# Get values from environment variables
anime_name = os.getenv('ANIME_NAME')
output_video_path = os.getenv('OUTPUT_VIDEO_PATH')
audio_path = os.getenv('AUDIO_PATH')

# if not all([anime_name, output_video_path, audio_path]):
#     raise ValueError("ANIME_NAME, OUTPUT_VIDEO_PATH, and AUDIO_PATH environment variables must be set")

if __name__ == "__main__":
    print("Anime Name:", anime_name)
    SubDownload.scrapData("DunderMifflin")
    S3Upload.consume_images("DunderMifflin")

    # Kafka Side
   # S3ToKafka.produce_image_data("CallOfDuty")
   # KafkaConsumer.consume_images("CallOfDuty", "/home/aditya/reddit-image-scrapper/RedditImageScrapper", "/home/aditya/reddit-image-scrapper/RedditImageScrapper/waydown.mp3")
    # rabbitProtest.produce_message()
    # rabbitConTest.consume_message()
