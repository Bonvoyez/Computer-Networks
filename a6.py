import socket
import threading
import struct

def recursive_dns_query(domain_name):
    # Construct DNS message
    message_id = 1234 # Choose a unique ID for the query
    flags = 0b0000000100000000 # Standard query with recursion desired
    questions = 1 # Only one question in the query
    answers = 0 # No answers in the query
    authorities = 0 # No authoritative records in the query
    additional = 0 # No additional records in the query
    
    # Split the domain name into individual labels and encode them as DNS format
    labels = domain_name.split('.')
    encoded_labels = b''
    for label in labels:
        encoded_labels += bytes([len(label)]) + label.encode('ascii')
    encoded_labels += b'\x00' # End of labels marker
    
    # Query type A (IPv4 address)
    query_type = 0x0001
    query_class = 0x0001 # Internet class
    
    # Pack the message fields into a binary string
    message = struct.pack('!HHHHHH', message_id, flags, questions, answers, authorities, additional)
    message += encoded_labels
    message += struct.pack('!HHi', query_type, query_class, 0)
    
    # Send message to DNS server
    root_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    root_server.sendto(message, ("e.root-servers.net", 53))
    print("REached")
    
    # Wait for response
    while True:
        try:
            response, addr = root_server.recvfrom(512)
        except socket.timeout:
            return 'Timeout waiting for response'
        
        # Parse response
        header = response[:12]
        print(response + "!!!!!!!!!")
        answer_count, = struct.unpack('!H', header[6:8])
        
        if answer_count > 0:
            # Answer found, extract IP address from response
            response_type, response_class, response_ttl, response_length = struct.unpack('!HHIH', response[-10:])
            ip_address = socket.inet_ntoa(response[-4:])
            return ip_address
        else:
            # No answer found, extract the address of the next DNS server to query
            response_type, response_class, response_ttl, response_length = struct.unpack('!HHIH', response[-10:])
            next_server = response[-response_length:-10].decode('ascii')
            if next_server == root_server:
                return 'Loop detected in DNS query chain'
            else:
                return recursive_dns_query(domain_name, next_server)


ip = "0.0.0.0"
port = 53
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((ip, port))

print(f"Server listening on {ip}:{port}")

while True:
    data, address = server_socket.recvfrom(1024)
    data = data.decode("ISO-8859-1")
    data = data[2:]
    while not data.endswith("com"):
        data = data[:-1]
    print(data)
    print(address)
    client_thread = threading.Thread(target=recursive_dns_query, args=[data])
    client_thread.start()