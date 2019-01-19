# A first try at WSPR transmission generation.

import encode
import numpy as np

### Message details
callsign = 'SM2YHP'
locator = 'KP07'
dbm = 30
base_freq = 14095600

### WSPR details
msg_len= 162
sample_rate = 32e6
fsk_shift = 1.4648
baud_len = int(8192.0/12000.0*sample_rate) # samples

### Encode message
fsks = encode.wspr_encode(callsign, locator, dbm)
assert len(fsks) == msg_len

### Write raw sample file
sample_file = f'{callsign}_{locator}_{dbm}_{base_freq}_{sample_rate}.dat'
sample_index = 0
loop = 1
with open(sample_file,'bw') as sf:
    for baud in fsks:
        freq = base_freq + baud*fsk_shift;
        phases = 2*np.pi*freq*(sample_index + np.arange(baud_len))/sample_rate
        samples = 128.0 + 128.0 * np.cos(phases)
        samples.astype(np.uint8).tofile(sf)        
        sample_index=sample_index + baud_len
        print(f'Written baud {loop} / 162 FSK {baud}')
        loop = loop + 1
