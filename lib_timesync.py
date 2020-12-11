# Version 1.3,  2020-05-14
from tis.oneM2M import *
from socket import *
from device.synch import *
import paho.mqtt.client as mqtt
import os, sys

global lib_topic
global lib_mqtt_client

argv = sys.argv

def on_connect(client,userdata,flags, rc):
    print('[msw_mqtt_connect] connect to ', broker_ip)
    sub_container_name = lib['control'][0]
    control_topic = '/MUV/control/' + lib['name'] + '/' + sub_container_name
    lib_mqtt_client.subscribe(control_topic, 0) 
    print ('[lib]control_topic\n', control_topic)

def on_disconnect(client, userdata, flags, rc=0):
	print(str(rc))


def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
    global missionPort
    message = str(msg.payload.decode("utf-8"))


def msw_mqtt_connect(broker_ip, port):
    global lib_topic
    global lib_mqtt_client

    lib_topic = ''

    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_subscribe = on_subscribe
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    lib_mqtt_client.loop_start()
    return lib_mqtt_client


def send_data_to_msw (data_topic, obj_data):
    global lib_mqtt_client
    
    lib_mqtt_client.publish(data_topic, obj_data)



if __name__ == '__main__':

    #os.system('sudo systemctl disable systemd-timesynch.service')
    os.system('sudo timedatectl set-ntp off')
    my_lib_name = 'lib_timesync'

    try:
        lib = dict()
        with open(my_lib_name + '.json', 'r') as f:
            lib = json.load(f)
            lib = json.loads(lib)

    except:
        lib = dict()
        lib["name"] = my_lib_name
        lib["target"] = 'armv6'
        lib["description"] = '[name] [server ip] [interval] [protocol] [threshold] [server port]'
        lib["scripts"] = './lib_timesync 203.253.128.177 1 udp 5 5005'
        lib["data"] = ['TimeSync']
        lib["control"] = ['']
        lib = json.dumps(lib, indent=4)
        lib = json.loads(lib)

        with open('./' + my_lib_name + '.json', 'w', encoding='utf-8') as json_file:
            json.dump(lib, json_file, indent=4)


    broker_ip = 'localhost'
    port = 1883

    # Inforamtion for time server
    monitor = Monitor()
    '''
    예시: argv[n] = [파라미터 = default value]
    argv[1] = [서버주소 = keti 서버]
    argv[2] = [업로드 주기 = 1초]
    argv[3] = [소켓 프로토콜 = udp]
    argv[4] = [동기화 문턱 값 = 5ms]
    argv[5] = [동기화 port = 5005]
    '''
    if len(argv) < 2: monitor.server_addr = '203.253.128.177'
    else : monitor.server_addr = argv[1]
    if len(argv) < 3: monitor.interval = 1   # Interval for offset report to Mobius (second)
    else : monitor.interval = int( argv[2] )
    if len(argv) < 4: monitor.trans_protocol = 'udp'
    else : monitor.trans_protocol = argv[3]
    if len(argv) < 5: monitor.threshold = 5  # Offset threshold for synchronization (millisecond)
    else : monitor.threshold = int( argv[4] )    
    if len(argv) < 6: monitor.server_port = '5005'
    else : monitor.server_port = argv[5]
    

    # Define resource
    container_name = lib["data"][0]
    monitor.topic = '/MUV/data/' + lib["name"] + '/' + container_name

    # TAS thread
    msw_mqtt_connect(broker_ip, port)
    monitor_tis = MUV_TIS(monitor, lib_mqtt_client).start()
