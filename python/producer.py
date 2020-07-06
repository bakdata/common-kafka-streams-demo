import glob
import os

import boto3
import click
from kafka import KafkaProducer


def get_files_in_dir(dir_path, file_filter):
    return glob.glob(f'{dir_path}/{file_filter}')


def on_send_error(excp):
    print('Failed to send message')
    print(excp)


def on_send_success(message, record_metadata):
    print(f'Add file {message} to topic')


@click.command()
@click.option('--broker_url', help='Kafka broker urls', required=True)
@click.option('--data_path', help='Path to the data', required=True)
@click.option('--s3_bucket', help='Bucket name', required=True)
@click.option('--s3_bucket_dir', help='Directory in the bucket', required=True)
@click.option('--topic', help='The topic the producer sends to', required=True)
@click.option('--short', default=None, help='Generate short texts for testing with <short> characters')
@click.option('--file_filter', default='*.txt', help='Filter to select specific files')
@click.option('--s3endpoint_url', default=None, help='Custom endpoint for s3')
def start_producer(broker_url, data_path, s3_bucket, s3_bucket_dir, topic, short, file_filter, s3endpoint_url):
    brokers = broker_url.split(',') if ',' in broker_url else broker_url
    producer = KafkaProducer(bootstrap_servers=brokers)

    files = get_files_in_dir(data_path, file_filter)

    s3_client = boto3.client('s3')
    if s3endpoint_url is not None:
        s3_client = boto3.client('s3', endpoint_url=s3endpoint_url)

    # check if bucket exists:
    if s3_bucket in [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]:
        print(f'Found {s3_bucket} bucket')
    else:
        print(f'Connection to bucket {s3_bucket} failed')
        return 0

    response = s3_client.list_objects(Bucket=s3_bucket, Prefix=s3_bucket_dir)
    already_existing_files = set([el['Key'] for el in response.get('Contents', [])])

    for file in files:
        filename = os.path.basename(file)
        key = f'{s3_bucket_dir}/{filename}'

        if key not in already_existing_files:
            print(f'Uploaded file {key}')
            # only use part of the file
            if short is not None:
                f = open(file, mode='r')
                file_content = f.read()[:int(short)]
                s3_client.put_object(Body=file_content.encode(), Bucket=s3_bucket, Key=key)
            else:
                s3_client.upload_file(file, s3_bucket, key)
        else:
            print(f'File {key} already exists in bucket')

        message = f's3://{s3_bucket}/{key}'.encode()
        producer.send(topic, key=message, value=message) \
            .add_callback(on_send_success, file) \
            .add_errback(on_send_error)
    producer.flush()


if __name__ == '__main__':
    start_producer()
