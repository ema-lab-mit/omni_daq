# %%
import os
import sys
# Setup paths
this_path = os.path.abspath(__file__)
# father_path = os.path.abspath(os.path.join(this_path, "../../"))
father_path = "C:\\Users\\EMALAB\\Desktop\\TW_DAQ"
# print(father_path)
sys.path.append(father_path)
# %%
################################
# Local imports
from TimeTaggerDriver_isolde.timetagger4 import TimeTagger as tg

import time
import numpy as np

class Tagger():
    def __init__(self):
        self.trigger_level = 0.5
        self.trigger_type = 1
        
        self.channels = [False, False, False, True]
        self.levels = [-1.5 for _ in range(4)] #[1,1,1,1]
        # self.type = [False,False,False,False]
        self.type = [True,True,True,True]
        self.starts = [0,0,0,0]
        self.stops = [100_000,100_000,100_000,100_000]
        
        self.card = None
        self.started = False
        
        self.initted = False
        self.init_card()
        self.initted = True
        
    def set_trigger_level(self,level):
        self.trigger_level = level
        
    def set_trigger_rising(self):
        self.set_trigger_type(type='rising')
        
    def set_trigger_falling(self):
        self.set_trigger_type(type='falling')
        
    def set_trigger_type(self,type='falling'):
        self.trigger_type = type == 'rising'
        
    def enable_channel(self, channel):
        self.channels[channel] = True
    
    def disable_channel(self, channel):
        self.channels[channel] = False
        
    def set_channel_level(self,channel,level):
        self.levels[channel] = level
                
    def set_channel_rising(self,channel):
        self.set_type(channel,type='rising')
        
    def set_channel_falling(self,channel):
        self.set_type(channel,type='falling')
            
    def set_type(self,channel,type='falling'):
        self.type[channel] = type == 'rising'
        
    def set_channel_window(self,channel,start=0,stop=100_000):
        self.starts[channel] = start
        self.stops[channel] = stop
        
    def init_card(self):
        kwargs = {}
        kwargs['trigger_level'] = self.trigger_level
        kwargs['trigger_rising'] = self.trigger_type
        for i,info in enumerate(zip(self.channels,self.levels,self.type,self.starts,self.stops)):
            ch,l,t,st,sp = info
            kwargs['channel_{}_used'.format(i)] = ch
            kwargs['channel_{}_level'.format(i)] = l
            kwargs['channel_{}_rising'.format(i)] = t
            kwargs['channel_{}_start'.format(i)] = st
            kwargs['channel_{}_stop'.format(i)] = sp

        if self.card is not None:
            print("Card is not none")
            self.stop()

        print("Communicating with card...")
        self.card = tg(**kwargs)
        print("Card", self.card)

                
    def start_reading(self):
        if not self.initted:
            print("Card is already started")
            self.init_card()
        print("Card initialized in progress")
        self.started = True
        self.card.startReading()
        print("Reading started")

    def stop_reading(self):
        self.card.stopReading()
        self.started = False

    def get_data(self, timeout = 2):
        start = time.time()
        while time.time()-start < timeout:
            if self.card is None:
                print("Card is None")
                time.sleep(0.0001)
                continue
                
            status, data = self.card.getPackets()
            print("status")
            print(status)
            if status == 0: # trigger detected, so there is data
                if data == []:
                    return None
                else:
                    # print(data)
                    return data
                    
            elif status == 1: # no trigger seen yet, go to sleep for a bit and try again
                print("No trigger seen yet")
                time.sleep(0.0001)
                
            else:
                raise
            
        return None
                
        if self.card is not None:
            self.card.stopReading()
            self.card.startReading()
        return None
        
    def stop(self):
        self.started = False
        if self.card:
            if self.started:
                self.card.stopReading()
                
            self.card.stop()
            self.card = None   
            
if __name__ == '__main__':
    tagger = Tagger()
    for i in range(1,4):
        tagger.enable_channel(i)
        tagger.set_channel_level(i,-2.25)
        tagger.set_channel_falling(i)
        tagger.set_channel_window(i,stop = 2*1000*1000)
        print(tagger, i)
    tagger.set_trigger_level(-0.5)
    tagger.set_trigger_falling()
    tagger.set_trigger_level(0.5)
    tagger.set_trigger_rising()
    tagger.start_reading()
    print("done")