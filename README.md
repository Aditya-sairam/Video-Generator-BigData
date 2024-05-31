# Video Generator from Reddit Images

This project scrapes image data from Reddit, passes it to RabbitMQ, stores the images in AWS S3, and then fetches the data to produce a video using Kafka.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)

## Overview

The project is designed to:
1. Scrape images from a specified Reddit subreddit.
2. Send the image data to RabbitMQ.
3. Store the images in an AWS S3 bucket.
4. Fetch the image data from S3 and produce a video using Kafka.

## Architecture

1. **Reddit Scraper**: Scrapes images from a specified subreddit.
2. **RabbitMQ**: Acts as a message broker for transferring image data.
3. **AWS S3**: Stores the scraped images.
4. **Kafka**: Used for producing and consuming image data to create a video.
5. **Video Generator**: Consumes image data from Kafka and generates a video.

## Setup and Installation

### Prerequisites

- Docker
- Docker Compose
- AWS account with S3 access
- Reddit API credentials

### Installation Steps

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Aditya-sairam/video-generator-BigData.git
    cd video-generator-BigData
    ```

2. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following:
    ```env
    AWS_ACCESS_KEY_ID=your_aws_access_key
    AWS_SECRET_ACCESS_KEY=your_aws_secret_key
    RABBITMQ_HOST=rabbitmq
    KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    ```

3. **Build and run the Docker containers**:
    ```bash
    docker-compose up --build
    ```

## Usage

1. **Enter the required details**:
    When prompted, enter the anime name, output video path, and audio path.
    
2. **Monitor the logs**:
    Check the Docker container logs to ensure that the services are running correctly.

## Technologies Used

- Python
- Docker
- RabbitMQ
- Kafka
- AWS S3
- Reddit API
- PRAW (Python Reddit API Wrapper)

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License.
