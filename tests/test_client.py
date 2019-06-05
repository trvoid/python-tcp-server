################################################################################
# Test TCP socket client.                                                      #
################################################################################

import sys
import time
import socket
import numpy as np
import threading

################################################################################
# Constants                                                                    #
################################################################################

RECV_BUFSIZE = 4096

REQUEST_MAGIC_NUMBER  = b'TRRQ'
RESPONSE_MAGIC_NUMBER = b'TRRS'
MESSAGE_HEADER_LENGTH = 16

STATUS_OK = 0
STATUS_SERVICE_ERROR = 1

################################################################################
# Functions                                                                    #
################################################################################

def build_request_message(file_a, file_b):
    request_id = np.random.randint(0, 1000000)
    send_request_id = request_id.to_bytes(4, byteorder='little')

    with open(file_a, mode='r') as cfile:
        file_a_text = cfile.read()
    file_a_data = file_a_text.encode('utf-8')
    send_file_a_data_len = len(file_a_data).to_bytes(4, byteorder='little')
    
    with open(file_b, mode='r') as cfile:
        file_b_text = cfile.read()
    file_b_data = file_b_text.encode('utf-8')
    send_file_b_data_len = len(file_b_data).to_bytes(4, byteorder='little')
    
    body_length = 4 + 4 + len(file_a_data) + len(file_b_data)
    send_body_length = body_length.to_bytes(4, byteorder='little')
    
    reserved_area = bytes([0, 0, 0, 0])
    
    send_data = (
        REQUEST_MAGIC_NUMBER + 
        send_request_id + 
        send_body_length +
        reserved_area +
        send_file_a_data_len + 
        send_file_b_data_len +
        file_a_data +
        file_b_data
    )
    
    return request_id, send_data

def parse_response_message(data):
    if len(data) < MESSAGE_HEADER_LENGTH:
        raise ValueError(f'Short message header length: expected = {MESSAGE_HEADER_LENGTH}, actual = {len(data)}')
        
    # Magic number
    magic_number = data[0:4]
    if magic_number != RESPONSE_MAGIC_NUMBER:
        raise ValueError(f'Illegal magic number: {magic_number.hex()}')
    
    # Request ID
    request_id = int.from_bytes(data[4:8], byteorder='little')
    
    # Result data length
    result_length = int.from_bytes(data[8:12], byteorder='little')
    
    expected_total_length = MESSAGE_HEADER_LENGTH + result_length
    if len(data) < expected_total_length:
        raise ValueError(f'Short total message length: expected = {expected_total_length}, actual = {len(data)}')
    
    # Status
    status = data[12]
    
    # Reserved area
    reserved_area = data[13:16]
    
    # Result data
    result_data_arr = data[16:16+result_length]
    result_data = result_data_arr.decode('utf-8')

    return request_id, status, result_data

def do_test(thread_name, connection_count, loop_per_connection, file_a, file_b):
    send_count = 0
    error_count = 0

    start_time = time.time()

    for k in range(connection_count):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))

        for i in range(loop_per_connection):
            send_count = send_count + 1
        
            request_id, tx_data = build_request_message(file_a, file_b)
        
            #client_socket.sendall(tx_data)
            client_socket.send(tx_data[0:10])
            time.sleep(0.005)
            client_socket.send(tx_data[10:50])
            time.sleep(0.01)
            client_socket.send(tx_data[50:500])
            time.sleep(0.05)
            client_socket.send(tx_data[500:])
        
            rx_data = client_socket.recv(RECV_BUFSIZE)
        
            _request_id, status, result_data = parse_response_message(rx_data)
        
            if status != STATUS_OK:
                error_count = error_count + 1
            print(f'[{thread_name}] send = {send_count:7}, error = {error_count:7}, result = {result_data}', end = '\r')
        
        client_socket.close()
    
    elapsed_time = time.time() - start_time
    
    print(f'[{thread_name}] send = {send_count:7}, error = {error_count:7}, result = {result_data}, elapsed_time = {elapsed_time:.3f} sec')

def print_usage(script_name):
  print(f'Usage: python {script_name} <ip> <port> <connection_count> <loop_per_connection>')

################################################################################
# Configuration                                                                #
################################################################################

file_a = 'file_a.txt'
file_b = 'file_b.txt'
    
thread_count = 4

################################################################################
# Main                                                                         #
################################################################################
  
if len(sys.argv) < 5:
  print_usage(sys.argv[0])
  sys.exit(-1)

host = sys.argv[1]
port = int(sys.argv[2])
connection_count = int(sys.argv[3])
loop_per_connection = int(sys.argv[4])

thread_list = []

for i in range(thread_count):
    thread_name = f'thread-{i:02}'
    t = threading.Thread(target = do_test, args = (thread_name, connection_count, loop_per_connection, file_a, file_b))
    thread_list.append(t)

for t in thread_list:
    t.start()

for t in thread_list:
    t.join()

print('Done!!!')
