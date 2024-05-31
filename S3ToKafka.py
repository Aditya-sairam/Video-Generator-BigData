import os
import boto3
import logging
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from botocore.exceptions import NoCredentialsError, ClientError

# AWS S3 Configuration
bucket_name = 'reddit-scrapped-images'
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = 'us-east-2'

# Initialize S3 client
s3_client = boto3.client('s3',
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key,
                         region_name=region_name)

# Initialize Kafka producer and admin client
kafka_bootstrap_servers = 'kafka:9092'
producer = KafkaProducer(
    bootstrap_servers=kafka_bootstrap_servers,
    value_serializer=lambda v: v  # No serialization needed, we are sending bytes
)
admin_client = KafkaAdminClient(bootstrap_servers=kafka_bootstrap_servers)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_kafka_topic(topic_name, num_partitions=3, replication_factor=1):
    try:
        topic_list = [NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)]
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        logger.info(f"Created Kafka topic: {topic_name} with {num_partitions} partitions")
    except Exception as e:
        logger.warning(f"Kafka topic {topic_name} might already exist or error in creation: {e}")

def get_image_data_from_s3(anime_name):
    try:
        prefix = f'{anime_name}/'
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                try:
                    image_data = s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])['Body'].read()
                    yield image_data
                except ClientError as e:
                    logger.error(f"Error fetching image {obj['Key']} from S3: {e}")
        else:
            logger.info(f"No images found for {anime_name}")
    
    except NoCredentialsError:
        logger.error("Credentials not available")
    except Exception as e:
        logger.error(f"Error fetching images from S3: {e}")

def produce_image_data(anime_name):
    topic_name = f'anime_{anime_name}'
    create_kafka_topic(topic_name, num_partitions=3)  # Create topic with 3 partitions
    
    try:
        for image_data in get_image_data_from_s3(anime_name):
            partition_key = image_data[:10]  # Use the first 10 bytes as the partition key
            producer.send(topic_name, key=partition_key, value=image_data)
            logger.info(f"Sent image data to Kafka topic {topic_name}")
        producer.flush()
    except Exception as e:
        logger.error(f"Error producing messages to Kafka: {e}")

# Usage example
if __name__ == "__main__":
    anime_name = input("Enter the anime name: ")
    produce_image_data(anime_name)
