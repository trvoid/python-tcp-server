################################################################################
# Test TCP socket client.                                                      #
################################################################################

import sys, time
import threading
from tcp_client import TcpClient

################################################################################
# Constants                                                                    #
################################################################################

STATUS_OK = 0
STATUS_SERVICE_ERROR = 1

################################################################################
# Functions                                                                    #
################################################################################

def build_request_data(file_a, file_b):
    with open(file_a, mode='r') as cfile:
        file_a_text = cfile.read()
    file_a_data = file_a_text.encode('utf-8')
    file_a_data_len = len(file_a_data).to_bytes(4, byteorder='little')
    
    with open(file_b, mode='r') as cfile:
        file_b_text = cfile.read()
    file_b_data = file_b_text.encode('utf-8')
    file_b_data_len = len(file_b_data).to_bytes(4, byteorder='little')
    
    request_data = (
        file_a_data_len + 
        file_b_data_len +
        file_a_data +
        file_b_data
    )
    
    return request_data

def do_test(thread_name, 
        host, port, 
        connection_count, loop_per_connection, 
        file_a, file_b):
    send_count = 0
    error_count = 0

    start_time = time.time()

    for k in range(connection_count):
        tcp_client = TcpClient(host, port)

        for i in range(loop_per_connection):
            send_count = send_count + 1
        
            body_data = build_request_data(file_a, file_b)
            
            tcp_client.send(body_data)
        
            status, result_data = tcp_client.recv()
        
            if status != STATUS_OK:
                error_count = error_count + 1
            print(f'[{thread_name}] send = {send_count:7}, error = {error_count:7}, result = {result_data}', end = '\r')
        
        tcp_client.close()
    
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
    t = threading.Thread(
            target = do_test, 
            args = (thread_name, 
                    host, port, 
                    connection_count, loop_per_connection, 
                    file_a, file_b)
        )
    thread_list.append(t)

for t in thread_list:
    t.start()

for t in thread_list:
    t.join()

print('Done!!!')
