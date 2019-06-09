################################################################################
# TCP socket client.                                                           #
################################################################################

import time, socket

################################################################################
# Constants                                                                    #
################################################################################

RECV_BUFSIZE = 4096

REQUEST_MAGIC_NUMBER  = b'TRRQ'
RESPONSE_MAGIC_NUMBER = b'TRRS'
MESSAGE_HEADER_LENGTH = 16

################################################################################
# Classes                                                                      #
################################################################################

class TcpClient:
    def __init__(self, host, port):
        self.request_counter = 0
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))

    def parse_response_message(self, data):
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
    
    def send(self, data):
        self.request_counter += 1
        request_id = self.request_counter.to_bytes(4, byteorder='little')
        
        body_length = len(data).to_bytes(4, byteorder='little')
        
        reserved_area = bytes([0, 0, 0, 0])
    
        tx_data = (
            REQUEST_MAGIC_NUMBER + 
            request_id + 
            body_length +
            reserved_area +
            data
        )
        
        #self.client_socket.sendall(tx_data)
        self.client_socket.send(tx_data[0:10])
        time.sleep(0.005)
        self.client_socket.send(tx_data[10:50])
        time.sleep(0.01)
        self.client_socket.send(tx_data[50:500])
        time.sleep(0.05)
        self.client_socket.send(tx_data[500:])
        
    def recv(self):
        rx_data = self.client_socket.recv(RECV_BUFSIZE)
        
        request_id, status, result_data = self.parse_response_message(rx_data)
        
        if request_id != self.request_counter:
            raise RuntimeError(f'Request ID mismatch: expected = {self.request_counter}, received = {request_id}')
        
        return status, result_data
        
    def close(self):
        self.client_socket.close()
        