isolde_tagger_drivers = True
from timetagger4 import TimeTagger as tg

import time
import numpy as np

class Tagger():
    def __init__(self):
        self.trigger_level = 0.5
        self.trigger_type = False
        
        self.channels = [1, False, False, 0]
        self.levels = [-.5 for _ in range(4)] #[1,1,1,1]
        self.type = [False,False,False,False]
        self.starts = [0,0,0,0]
        self.stops = [100_000,100_000,100_000,100_000]
        
        self.card = None
        self.started = False

        self.init_card()
        
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

        print(kwargs)
        self.card = tg(**kwargs)

                
    def start_reading(self):
        self.init_card()
        self.started = True
        self.card.startReading()

    def stop_reading(self):
        self.card.stopReading()
        self.started = False

    def get_data(self,timeout = 2):
        start = time.time()
        while time.time()-start < timeout:
            if self.card is None:
                time.sleep(0.0001)
                continue
                
            status, data = self.card.getPackets()
            if status == 0: # trigger detected, so there is data
                if data == []:
                    return None
                else:
                    # print(data)
                    return data
                    
            elif status == 1: # no trigger seen yet, go to sleep for a bit and try again
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
    tag = Tagger()