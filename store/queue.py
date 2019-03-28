import time

import pika
import json


def store_data_in_queue(instance):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='urban_piper', arguments={'x-max-priority': 10})

    result = json.dumps({"id": instance.id, "title": instance.title,
                         "priority": instance.priority, "last_known_state": instance.last_known_state})

    channel.basic_publish(exchange='',
                          routing_key='urban_piper',
                          body=result,
                          properties=pika.BasicProperties(delivery_mode=2,
                                                          priority=get_priority_value(instance.priority)))

    connection.close()
    return True


def read_data_from_queue(acknowledge=False):
    connection = pika.BlockingConnection()
    channel = connection.channel()
    method_frame, header_frame, body = channel.basic_get('urban_piper')

    if method_frame:
        if acknowledge:
            channel.basic_ack(1)
            return True
        else:
            channel.basic_ack(0)
            result = body.decode('utf-8')
            json_data = json.loads(result)
            return json_data
    else:
        return False



def get_priority_value(priority):
    if priority == "HIGH":
        return 3
    elif priority == "MEDIUM":
        return 2
    elif priority == "LOW":
        return 1
    else:
        return 0
