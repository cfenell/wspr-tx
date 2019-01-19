# WSPR transmission over fl2k_tcp

import encode
import numpy as np
import time
import socket


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


### Waveform writer
def sample_producer(msg, base_freq, sample_rate):

    ## WSPR details
    msg_len= 162
    fsk_shift = 1.4648
    baud_len = int(8192.0/12000.0*sample_rate) # samples

    assert len(msg) == msg_len

    wave = np.array(zeros(msg_len * baud_len), dtype=np.uint8)
    baud_no=1
    sample0=0
    sample=np.arange(baud_len)
    
    for baud in msg:
        freq = base_freq + baud*fsk_shift;
        phases = 2*np.pi*freq*(sample0 + sample)/sample_rate
        wave[sample0:sample0+baud_len] = ( 128.0 + 128.0 * np.cos(phases) ).astype(np.uint8)
        sample0=sample0 + baud_len
        print(f'sample_producer: Done baud {baud_no} FSK shift {baud}')
        baud_no=baud_no + 1
        

    return(wave)
    
if __name__ == '__main__':

    ### Set up TCP server
    print(f'wsprtcp: Creating sample server on {tcp_host}:{tcp_port}')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((tcp_host, tcp_port))
    s.listen(1)
    conn, addr = s.accept()

    ### Encode message
    print(f'wsprtcp: Encoding message {callsign} {locator} {dbm}')
    msg = encode.wspr_encode(callsign, locator, dbm)

    ### Pre-create waveform
    print(f'wsprtcp: Creating waveform f={base_freq} Hz at {sample_rate} Hz. This will take time.')
    wave=sample_producer(msg, base_freq, sample_rate):

    ### Main loop
    for loop_no in range(nloops):

        ## Wait for time to start Tx  
        print(f'wsprtcp: Waiting to start cycle {loop_no+1} of {nloops}')

        while(True):
            if time.time() % 120 < 0.05:
                break
            time.sleep(0.01)

        print(f'wsprtcp: Transmitting message')
        conn.sendall(wave)
        print(f'wsprtcp: Done cycle {loop_no+1} of {nloops}')
        
    ### Done
    conn.close()
    print('wsprtcp: Done')

