import pika
import os

# Connection parameters
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
QUEUE_NAME = "test_queue"

# Callback function to process messages
def callback(ch, method, properties, body):
    print(f"Received message: {body}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_message():
# Establish connection to RabbitMQ
    connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # Declare a queue
    channel.queue_declare(queue=QUEUE_NAME)

    # Start consuming messages
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

