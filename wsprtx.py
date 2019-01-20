### WSPR transmission over fl2k_tcp
### C-F Enell 20190120

### Default libraries
import numpy as np
import socket
import subprocess
import time
from os.path import isfile

### Modules
import encode
import wspr_config

### Waveform writer
def sample_producer(msg, base_freq, sample_rate):

    ## WSPR details
    msg_len= 162
    fsk_shift = 1.4648
    baud_len = int(8192.0/12000.0*sample_rate) # samples

    assert len(msg) == msg_len

    ## Open waveform file if exists
    wfile=f'/tmp/wspr_{base_freq}_{sample_rate}.dat'

    if isfile(wfile):
        wave=np.memmap(filename=wfile, dtype='uint8')
        if len(wave)==msg_len*baud_len:
            print('sample_producer: waveform file found.')
            return(wave, baud_len)
        else:
            # Bad file, will be overwritten next
            del(wave)           
        
    ## Else create waveform file
    print('sample_producer: Creating waveform file. This will take time.')
    wave = np.memmap(filename=wfile, mode='w+', dtype='uint8', shape=(msg_len*baud_len))
    baud_no=1
    sample0=0
    si=np.arange(baud_len)

    ## Fill waveform with 4FSK samples 
    for baud in msg:
        freq = base_freq + baud*fsk_shift;
        phases = 2*np.pi*freq*(sample0 + si)/sample_rate
        ## 8-bit samples
        wave[sample0:sample0+baud_len] = ( 128.0 + 128.0 * np.cos(phases) ).astype(np.uint8)
        sample0=sample0 + baud_len
        print(f'sample_producer: Done baud {baud_no}:{msg_len} 4FSK shift {baud}')
        baud_no=baud_no + 1
        
    return(wave, baud_len)
    
if __name__ == '__main__':

    ### Prepare WSPR message Tx
    
    ## Encode message
    print(f'wsprtcp: Encoding message {wspr_config.callsign} {wspr_config.locator} {wspr_config.dbm}')
    msg = encode.wspr_encode(wspr_config.callsign, wspr_config.locator, wspr_config.dbm)

    ## Pre-create waveform
    print(f'wsprtcp: Getting waveform f={wspr_config.base_freq} Hz at {wspr_config.sample_rate} Hz.')
    wave, baud_len=sample_producer(msg, wspr_config.base_freq, wspr_config.sample_rate) #mmap

    ## Set up TCP server
    print(f'wsprtcp: Creating sample server on {wspr_config.tcp_host}:{wspr_config.tcp_port}')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((wspr_config.tcp_host, wspr_config.tcp_port))
    s.listen(1)

    ## Spawn the fl2k client
    client_args=[wspr_config.tcp_client,'-a',wspr_config.tcp_host,'-p',f'{wspr_config.tcp_port}','-d',f'{wspr_config.fl2k_dev}','-s',f'{wspr_config.sample_rate}']
    print(f'wsprtcp: Spawning {client_args}')
    tcp_client=subprocess.Popen(client_args)

    ## Connect client
    conn, addr = s.accept()
        
    ### Main loop
    for loop_no in range(wspr_config.nloops):

        ## Wait for time to start Tx  
        print(f'wsprtcp: Waiting to start cycle {loop_no+1} of {wspr_config.nloops}')
        while(True):
            if time.time() % 120 < 0.05:
                break
            time.sleep(0.01)

        ## Transmit one sequence
        print('wsprtcp: Transmitting message')
        bufstart=0
        stop = False
        while True:
            ## Send one FSK baud to FL2K
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
        ## Done transmit sequence
        print(f'wsprtcp: Done cycle {loop_no+1} of {wspr_config.nloops}')

    ###  Done main loop
    wave.flush() # Make sure to save on disk
    del(wave)    # Close mmapped file
    conn.close()
    tcp_client.terminate()
    print('wsprtcp: Done')
### End of wsprtcp.py
