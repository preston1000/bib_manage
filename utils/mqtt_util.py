import random
import json
import time

from paho.mqtt import client as mqtt_client

"""
# Error values -- for 'build_flag'
MQTT_ERR_AGAIN = -1
MQTT_ERR_SUCCESS = 0
MQTT_ERR_NOMEM = 1
MQTT_ERR_PROTOCOL = 2
MQTT_ERR_INVAL = 3
MQTT_ERR_NO_CONN = 4
MQTT_ERR_CONN_REFUSED = 5
MQTT_ERR_NOT_FOUND = 6
MQTT_ERR_CONN_LOST = 7
MQTT_ERR_TLS = 8
MQTT_ERR_PAYLOAD_SIZE = 9
MQTT_ERR_NOT_SUPPORTED = 10
MQTT_ERR_AUTH = 11
MQTT_ERR_ACL_DENIED = 12
MQTT_ERR_UNKNOWN = 13
MQTT_ERR_ERRNO = 14
MQTT_ERR_QUEUE_SIZE = 15

"""


class MqttUtil:
    client = None

    def __init__(self, broker, port, client_id=None, on_publish=None, on_message=None):

        def on_connect(ct, userdata, flags, rc):
            """
            Called when the broker responds to our connection request.
            :param ct: the client instance for this callback
            :param userdata: the private user data as set in Client() or user_data_set()
            :param flags: dict that contains response flags sent by the broker.
                flags['session present'] - this flag is useful for clients that are using clean session set to 0 only
            :param rc:  0: Connection successful
                        1: Connection refused - incorrect protocol version
                        2: Connection refused - invalid client identifier
                        3: Connection refused - server unavailable
                        4: Connection refused - bad username or password
                        5: Connection refused - not authorised
                        6-255: Currently unused.
            :return:
            """
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        def on_disconnect(ct, userdata, rc):
            """
            Called when the client disconnects from the broker.
            :param ct: the client instance for this callback
            :param userdata: the private user data as set in Client() or user_data_set()
            :param rc: the disconnection result
            :return:
            """
            if rc != 0:
                print("Unexpected disconnection.")
            else:
                print("disconnected normally")

        def on_publish_default(ct, userdata, mid):
            """

            :param ct: the client instance for this callback
            :param userdata: user defined data which isn’t normally used
            :param mid: the message id and can be used with the mid value returned from the publish method to check that
                    a particular message has been published.
            :return:
            """
            if mid is not None and mid > 0:
                print("successfully published")
            else:
                print("failed to publish")

        def on_message_default(ct, userdata, msg):
            """
            Called when a message has been received on a topic that the client subscribes to and the message does not
            match an existing topic filter callback.
            :param ct: the client instance for this callback
            :param userdata: the private user data as set in Client() or user_data_set()
            :param msg: an instance of MQTTMessage. This is a class with members topic, payload, qos, retain.
            :return:
            """
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic with Qos " + str(msg.qos))

        # Set Connecting Client ID
        if client_id is None:
            client_id = f'tu-command-{random.randint(0, 1000)}'
            print("未指定client id，随机生成")

        # initialize client
        ct = mqtt_client.Client(client_id)
        ct.on_connect = on_connect
        ct.on_disconnect = on_disconnect

        # connect to broker
        build_flag = ct.connect(broker, port)

        if on_publish is None:
            ct.on_publish = on_publish_default
        else:
            ct.on_publish = on_publish

        if on_message is None:
            ct.on_message = on_message_default
        else:
            ct.on_message = on_message

        if build_flag == 0:
            print("successfully build the connection")
            ct.loop_start()
            self.client = ct
        else:
            print("failed to build connection")

    def publish(self, topic, msg):
        """
        publish to broker
        :param topic: str
        :param msg: str
        :return:
        """
        if topic is None or msg is None:
            print("invalid topic or payload")
            return -2

        if not isinstance(msg, str):
            print("payload should be str")
            return -3

        result = self.client.publish(topic, msg)

        if result[0] == 0:
            print(f"Sent `{msg}` to topic `{topic}` successfully")
            flag = 0
        else:
            print(f"Failed to send message to topic {topic}")
            flag = -1
        return flag

    def subscribe(self, topic):
        """
        subscribe to broker
        :param topic: str
        :return:
        """
        self.client.subscribe(topic)


if __name__ == '__main__':
    broker = '10.11.80.108'  # 连接地址
    port = 1883  # 端口地址
    topic = "/tu/command"  # 主题topic
    client_id = f'tu-command-{random.randint(0, 1000)}'

    client = MqttUtil(broker, port, client_id)

    count = 1
    while count < 1000:
        msg = {"code": count, "data": {"action": "讲解"}}
        msg = json.dumps(msg, ensure_ascii=False)
        client.publish(topic, msg)
        count += 1
        time.sleep(1)
