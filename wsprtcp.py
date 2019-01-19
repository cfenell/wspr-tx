# WSPR transmission over fl2k_tcp

import encode
import numpy as np
import time
import socket
from multiprocessing import Process, Queue, Event, Lock

### fl2k_tcp config
tcp_host = '127.0.0.1'
tcp_port = 4242

### Message defaults
callsign = 'SM2YHP'
locator = 'KP07'
dbm = 30
base_freq = 7038600
sample_rate = 16e6
nloops = 5

### Sample queue writer

def sample_producer(msg_queue, event, lock, msg, base_freq, sample_rate):

    ## WSPR details
    msg_len= 162
    fsk_shift = 1.4648
    baud_len = int(8192.0/12000.0*sample_rate) # samples

    assert len(msg) == msg_len

    sample_index=0
    baud_no=1
    event.set()
    
    for baud in msg:
        freq = base_freq + baud*fsk_shift;
        phases = 2*np.pi*freq*(sample_index + np.arange(baud_len))/sample_rate
        samples = ( 128.0 + 128.0 * np.cos(phases) ).astype(np.uint8)
        msg_queue.put(samples)
        sample_index=sample_index + baud_len
        lock.acquire()
        print(f'sample_producer: Done baud {baud_no} FSK shift {baud}')
        lock.release()
        baud_no=baud_no + 1
        

def sample_server(msg_queue, event, lock, tcp_port):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((tcp_host, tcp_port))
    s.listen(1)
    conn, addr = s.accept()
    lock.acquire()
    print(f'sample_server: Opened TCP port {tcp_port}')
    lock.release()
 
    while True:
        lock.acquire()
        print('sample_server: waiting for next period')
        lock.release()
        
        event.wait()
        lock.acquire()
        event.clear()
        lock.release()
        
        while True:
            samples = msg_queue.get()
            if not len(samples):
                break
            conn.sendall(samples)
            lock.acquire()
            print(f'sample_server: Output Tx samples to TCP port {tcp_port}')
            lock.release()


        lock.acquire()
        print('sample_server: Done Tx samples')
        lock.release()
            

    ## cleanup
    conn.close()
    lock.acquire()
    print(f'sample_server: TCP port {tcp_port} closed')
    lock.release()

    
if __name__ == '__main__':    

    ### Encode message
    msg = encode.wspr_encode(callsign, locator, dbm)

    ### Map subprocesses
    msg_queue = Queue()
    event = Event()
    event.clear()
    lock = Lock()
    prod = Process(target=sample_producer, args=(msg_queue, event, lock,  msg, base_freq, sample_rate))
    cons = Process(target=sample_server, args=(msg_queue, event, lock, tcp_port))

    ### Start the server
    print('wsprtcp: Starting sample server')
    cons.start()
    
    ### Main loop
    for loop_no in range(nloops):

        ## Wait for time to start Tx
        lock.acquire()
        print(f'wsprtcp: Waiting to start cycle {loop_no+1} of {nloops}')
        lock.release()
        
        while(True):
            if time.time() % 120 < 0.05:
                break
            time.sleep(0.01)

        ## Start next Tx cycle
        # Start sample queue writer
        lock.acquire()
        print('wsprtcp: Starting sample writer')
        lock.release()
        prod.start()

        # Wait for sample queue writer to finish
        prod.join()
        lock.acquire()
        print('wsprtcp: Sample producer finished')
        lock.release()
        
    
    ### Stop server
    cons.terminate()
    print('wsprtcp: Done')







    

