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

    ### Encode message
    msg = encode.wspr_encode(callsign, locator, dbm)

    ### Pre-create waveform (this takes time)
    wave=sample_producer(msg, base_freq, sample_rate):

    




    

