import os
import boto3
import logging
import pika
import threading
import time
import requests
from botocore.exceptions import NoCredentialsError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 Configuration
bucket_name = 'reddit-video-maker'
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = 'us-east-2'

# Initialize S3 client
s3_client = boto3.client('s3',
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key,
                         region_name=region_name)

# Initialize RabbitMQ connection and channel
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', '172.17.0.2')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
QUEUE_NAME = "new_final_test"

connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()



# Declare the queue
channel.queue_declare(queue=QUEUE_NAME, durable=True)

output_dir = 'received_images'
os.makedirs(output_dir, exist_ok=True)

timeout = 30  # Timeout in seconds
last_message_time = time.time()

def upload_to_s3(image_name, image_data, bucket_name, s3_folder):
    try:
        s3_path = os.path.join(s3_folder, image_name).replace("\\", "/")
        s3_client.put_object(Bucket=bucket_name, Key=s3_path, Body=image_data)
        logger.info(f"Uploaded {image_name} to s3://{bucket_name}/{s3_path}")
    except NoCredentialsError:
        logger.error("Credentials not available")

def create_callback(s3_folder):
    def callback(ch, method, properties, body):
        global last_message_time
        try:
            message = body.decode('utf-8')
            image_name, image_url = message.split()
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                upload_to_s3(image_name, response.content, bucket_name, s3_folder)
            else:
                logger.error(f"Failed to download image from {image_url}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
            last_message_time = time.time()

        except Exception as e:
            logger.error(f'Error processing message: {e}')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    return callback

def check_s3_folder_exists(anime_name):
    try:
        prefix = f'{anime_name}/'
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response and response['KeyCount'] > 0:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error checking S3 folder: {e}")
        return False

def consume_images(s3_folder):
    global last_message_time
    stopping = False

    while not stopping:
        method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=False)
        if method_frame:
            callback = create_callback(s3_folder)
            callback(channel, method_frame, header_frame, body)
            last_message_time = time.time()
        else:
            if time.time() - last_message_time > timeout:
                logger.info('Timeout reached, stopping the consumer')
                stopping = True
            else:
                time.sleep(1)  # Sleep for a while before checking again

    connection.close()
    logger.info('Connection closed')

# Main function to check S3 folder and decide whether to consume from RabbitMQ
def main(anime_name):
    if check_s3_folder_exists(anime_name):
        logger.info(f"Folder for {anime_name} already exists in S3. No need to consume from RabbitMQ.")
        # Optionally, you can add code to process existing S3 data here if needed
    else:
        logger.info(f"Folder for {anime_name} does not exist in S3. Consuming from RabbitMQ.")
        consume_images(anime_name)

# Usage example
# if __name__ == "__main__":
#     anime_name = 'NewNaruto'  # Replace with the actual anime name
#     main(anime_name)

#consume_images("CallOfDuty")