################################################################################
# TCP socket server.                                                           #
#                                                                              #
# Features:                                                                    #
#   1. Using select.                                                           #
#   2. Single threaded.                                                        #
#   3. Event driven.                                                           #
################################################################################

import sys, traceback, logging
import select, socket, queue

################################################################################
# Constants                                                                    #
################################################################################

RECV_BUFSIZE = 4096

REQUEST_MAGIC_NUMBER  = b'TRRQ'
RESPONSE_MAGIC_NUMBER = b'TRRS'
MESSAGE_HEADER_LENGTH = 16

################################################################################
# Functions                                                                    #
################################################################################

class TcpServer:
    def __init__(self, name):
        self.logger = logging.getLogger()
        self.name = name

    def create_server(self, host, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(0)
        server.bind((host, port))
        server.listen(5)
        
        return server        
        
    def run(self, port, handler_factory):
        rlist = []
        wlist = []
        client_handlers = {}
        
        server = self.create_server('', port)
        rlist.append(server)
        self.logger.info(f'Listening on {server.getsockname()}')
        
        shutdownFlag = False
        
        while rlist:
            readable, writable, exceptional = select.select(rlist, wlist, rlist, 1)
            
            # readable
            for s in readable:
                if s is server:
                    connection, address = s.accept()
                    self.logger.info(f'new client {address}')
                    connection.setblocking(0)
                    rlist.append(connection)
                    client_handlers[connection] = handler_factory.create(connection)
                else:
                    count = client_handlers[s].read_ready()
                    if count == 0:
                        self.logger.info(f'close eof client {client_handlers[s].address}')
                        del client_handlers[s]
                        rlist.remove(s)
                        s.close()
                        
                        if s in writable:
                            writable.remove(s)
                        if s in exceptional:
                            exceptional.remove(s)
                    elif count < 0:
                        shutdownFlag = True

            # writable
            for s in writable:
                client_handlers[s].write_ready()
            
            # exceptional
            for s in exceptional:
                self.logger.info(f'close exceptional client {client_handlers[s].address}')
                del client_handlers[s]
                rlist.remove(s)
                s.close()
            
            # build wlist
            wlist.clear()
            for connection, client_handler in client_handlers.items():
                if not client_handler.tx_queue.empty():
                    wlist.append(connection)
            
            #print(f'** len(rlist) = {len(rlist):4}, len(wlist) = {len(wlist):4} **')
            
            if len(wlist) == 0 and shutdownFlag:
                break
        
        # Close all sockets
        for s in rlist:
            s.close()

class RequestMessage:
    def __init__(self, request_id, body_length):
        self.request_id = request_id
        self.body_length = body_length
        self.body_data = None
    
    def create_response(self):
        return ResponseMessage(self.request_id)
        
class ResponseMessage:
    def __init__(self, request_id):
        self.request_id = request_id
        
    def build_message(self, body_data):
        send_request_id = self.request_id.to_bytes(4, byteorder='little')
        
        result_length = len(body_data)
        send_result_length = result_length.to_bytes(4, byteorder='little')
        
        reserved_area = bytes([0, 0, 0, 0])
        
        tx_data = (
            RESPONSE_MAGIC_NUMBER + 
            send_request_id + 
            send_result_length + 
            reserved_area + 
            body_data
        )
        
        return tx_data
    
class ClientHandler:
    def __init__(self, connection, service):
        self.logger = logging.getLogger()
        self.connection = connection
        self.address = connection.getpeername()
        self.service = service
        self.rx_data = []
        self.request = None
        self.tx_queue = queue.Queue()
                
    def read_ready(self):
        try:
            data = self.connection.recv(RECV_BUFSIZE)
            if data:
                self.rx_data += list(data)
                
                if len(self.rx_data) >= MESSAGE_HEADER_LENGTH:
                    if not self.request:
                        self.request = self.parse_header(bytes(self.rx_data[0:MESSAGE_HEADER_LENGTH]))
                    
                    if len(self.rx_data) == (MESSAGE_HEADER_LENGTH + self.request.body_length):
                        self.request.body_data = bytes(self.rx_data[MESSAGE_HEADER_LENGTH:])
                        result_data = self.service.process(self.request)
                        
                        response = self.request.create_response()
                        tx_data = response.build_message(result_data)
    
                        self.rx_data.clear()
                        self.request = None
                        self.tx_queue.put(tx_data)
                
                return len(data)
            else:
                return 0
        except Exception as ex:
            self.logger.error(f'{self.address} Exception occurred.')
            self.logger.error(traceback.format_exc())
            return 0
            
    def write_ready(self):
        try:
            tx_data = self.tx_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            self.connection.sendall(tx_data)
    
    def parse_header(self, data):
        magic_number = data[0:4]
        if magic_number != REQUEST_MAGIC_NUMBER:
            raise ValueError(f'Illegal magic number: {magic_number.hex()}')
        
        request_id = int.from_bytes(data[4:8], byteorder='little')
        
        body_length = int.from_bytes(data[8:12], byteorder='little')
        
        return RequestMessage(request_id, body_length)
        
class ClientHandlerFactory:
    def __init__(self, service):
        self.service = service
        
    def create(self, connection):
        return ClientHandler(connection, self.service)
