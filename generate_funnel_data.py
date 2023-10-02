import json
import time
import random
import csv

from confluent_kafka import Producer


def acked(err, msg):
    if err is not None:
        print(f"Failed to deliver message: {msg.value()}: {err.str()}")


producer = Producer({'bootstrap.servers': 'localhost:9092'})

with open('data/funnel_steps.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        print(f'Sending payload: {row}')
        # Send to Kafka
        payload = json.dumps(row)
        producer.produce(topic='clickstream-events', key=str(row['user_id']),
                         value=payload, callback=acked)

        # Random sleep
        sleep_time = random.randint(1, 4)
        time.sleep(sleep_time)