import praw
import requests
import boto3
import cv2
import numpy as np
import os
import pickle
import pika  # Import pika for RabbitMQ
import logging
import time
import os
import pika
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable




logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POST_SEARCH_AMOUNT = 1250
#RABBITMQ_HOST = 'localhost'  # RabbitMQ Docker container IP address

bucket_name = 'reddit-scrapped-images'
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = 'us-east-2'

# Initialize S3 client
s3_client = boto3.client('s3',
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key,
                         region_name=region_name)



# RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')

# connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', '172.17.0.2')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
QUEUE_NAME = "test_queue"

connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()

# Declare a queue
channel.queue_declare(queue='new_final_test', durable=True)


def check_s3_folder_exists(folder_name):
    prefix = f'{folder_name}/'
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    return 'Contents' in response


# Function to publish data to RabbitMQ
def publish_to_rabbitmq(queue, data):
    channel.basic_publish(
        exchange='',
        routing_key=queue,
        body=data,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        ))
    print(f"Sent {data} to RabbitMQ")

# Create directory if it doesn't exist to save images
def create_folder(image_path):
    CHECK_FOLDER = os.path.isdir(image_path)
    if not CHECK_FOLDER:
        os.makedirs(image_path)

# Path to save images
dir_path = os.path.dirname(os.path.realpath(__file__))
image_path = os.path.join(dir_path, "images/")
ignore_path = os.path.join(dir_path, "ignore_images/")
create_folder(image_path)

# Get token file to log into reddit
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
else:
    creds = create_token()
    pickle_out = open("token.pickle", "wb")
    pickle.dump(creds, pickle_out)

def scrapData(topic):
    reddit = praw.Reddit(client_id=creds['client_id'],
                         client_secret=creds['client_secret'],
                         user_agent="Hello",
                         username=creds['username'],
                         password=creds['password'])

    sub = topic
    subreddit = reddit.subreddit(sub)

    print(f"Starting {sub}!")
    count = 0
    if check_s3_folder_exists(topic):
        logger.info(f"Folder {topic} already exists in S3. Skipping Reddit and RabbitMQ.")
        #consume_from_kafka(topic)
    else:
        for submission in subreddit.new(limit=POST_SEARCH_AMOUNT):
            if "jpg" in submission.url.lower() or "png" in submission.url.lower():
                try:
                    resp = requests.get(submission.url.lower(), stream=True).raw
                    image = np.asarray(bytearray(resp.read()), dtype="uint8")
                    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

                    # Could do transforms on images like resize
                    compare_image = cv2.resize(image, (224, 224))

                    # Get all images to ignore
                    #for (dirpath, dirnames, filenames) in os.walk(ignore_path):
                       # ignore_paths = [os.path.join(dirpath, file) for file in filenames]
                    ignore_flag = False

                    # for ignore in ignore_paths:
                    #     ignore = cv2.imread(ignore)
                    #     difference = cv2.subtract(ignore, compare_image)
                    #     b, g, r = cv2.split(difference)
                    #     total_difference = cv2.countNonZero(b) + cv2.countNonZero(g) + cv2.countNonZero(r)
                    #     if total_difference == 0:
                    #         ignore_flag = True

                    if not ignore_flag:
                        # Save image
                        image_filename = f"{sub}-{submission.id}.png"
                        
                        # Publish data to RabbitMQ
                        rabbitmq_data = f"{sub}-{submission.id} {submission.url.lower()}"
                        publish_to_rabbitmq('new_final_test', rabbitmq_data)
                        print(image_filename + " pushed to RabbitMQ")
                        count += 1
                        
                except Exception as e:
                    print(f"Image failed. {submission.url.lower()}")
                    print(e)

# Close RabbitMQ connection
    connection.close()


#scrapData("CallOfDuty")
