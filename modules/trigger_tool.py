
class Trigger:
    
    def __init__(self):
        self.sta = []
        self.lta = []
        self.data_buffer = []
        
    def sliding_window(self, sta_len, lta_ln, snr):

        self.sta.append(snr)
        self.lta.append(snr)

        # Check if the window buffer is full
        if len(self.sta) >= sta_len:
            # Clear the window buffer for the next window
            self.sta = self.sta[1:]  # Remove the oldest data point

        if len(self.lta) >= lta_ln:
            # Clear the window buffer for the next window
            self.lta = self.lta[1:]  # Remove the oldest data point
    
    def trigger_check(self, status):
        if not self.sta or not self.lta:
            return status

        staMean = sum(self.sta)/len(self.sta)
        ltaMean = sum(self.lta)/len(self.lta)

        if staMean/ltaMean > 1.35:
            status = True
        elif staMean/ltaMean < 1.1:
            status = False

        print(f'''status: {status}, STA/LTA: {staMean/ltaMean}, staMean:{staMean}, ltaMean:{ltaMean}''')
        return status
    
    def param_reset(self):
        self.sta = []
        self.lta = []
        self.data_buffer = []