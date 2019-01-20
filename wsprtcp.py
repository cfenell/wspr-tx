### WSPR transmission over fl2k_tcp
### C-F Enell 20190120

# Default libraries
import numpy as np
import mmap
import time
import socket

# Modules
import wspr_config
import encode


### Waveform writer
def sample_producer(msg, base_freq, sample_rate):

    ## WSPR details
    msg_len= 162
    fsk_shift = 1.4648
    baud_len = int(8192.0/12000.0*sample_rate) # samples

    assert len(msg) == msg_len

    wave = mmap.mmap(-1, msg_len * baud_len)
    baud_no=1
    sample0=0
    si=np.arange(baud_len)
    
    for baud in msg:
        freq = base_freq + baud*fsk_shift;
        phases = 2*np.pi*freq*(sample0 + si)/sample_rate
        wave[sample0:sample0+baud_len] = ( 128.0 + 128.0 * np.cos(phases) ).astype(np.uint8)
        sample0=sample0 + baud_len
        print(f'sample_producer: Done baud {baud_no} FSK shift {baud}')
        baud_no=baud_no + 1
        
    return(wave, baud_len)
    
if __name__ == '__main__':

    ### Set up TCP server
    print(f'wsprtcp: Creating sample server on {wspr_config.tcp_host}:{wspr_config.tcp_port}')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((wspr_config.tcp_host, wspr_config.tcp_port))
    s.listen(1)
    conn, addr = s.accept()

    ### Encode message
    print(f'wsprtcp: Encoding message {wspr_config.callsign} {wspr_config.locator} {wspr_config.dbm}')
    msg = encode.wspr_encode(wspr_config.callsign, wspr_config.locator, wspr_config.dbm)

    ### Pre-create waveform
    print(f'wsprtcp: Creating waveform f={wspr_config.base_freq} Hz at {wspr_config.sample_rate} Hz. This will take time.')
    wave, baud_len=sample_producer(msg, wspr_config.base_freq, wspr_config.sample_rate) #mmap

    ### Main loop
    for loop_no in range(wspr_config.nloops):

        ## Wait for time to start Tx  
        print(f'wsprtcp: Waiting to start cycle {loop_no+1} of {wspr_config.nloops}')

        while(True):
            if time.time() % 120 < 0.05:
                break
            time.sleep(0.01)

        print(f'wsprtcp: Transmitting message')

        bufstart=0
        stop = False
        while True:
            bufend = bufstart + baud_len
            if bufend > len(wave):
                bufend = len(wave)
                stop = True
            buf=wave[bufstart:bufend]
            conn.sendall(buf)
            print(f'wsprtcp: sent from sample {bufstart}')
            if stop:
                break
            bufstart=bufend
            
        print(f'wsprtcp: Done cycle {loop_no+1} of {nloops}')
        
    ### Done
    wave.close()
    conn.close()
    print('wsprtcp: Done')

