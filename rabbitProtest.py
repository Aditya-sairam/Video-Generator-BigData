import pika

# Connection parameters
import os
import pika

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
QUEUE_NAME = "test_queue"

connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()

# Your existing code

# Declare a queue
channel.queue_declare(queue=QUEUE_NAME)

def produce_message():
# Send a message
    message = 'Hello, RabbitMQ!'
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=message)
    print(f"Sent message: {message}")

# Close the connection
    connection.close()

produce_message()