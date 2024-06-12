import os
import sys
# Setup paths
this_path = os.path.abspath(__file__)
father_path = os.path.abspath(os.path.join(this_path, "../../"))
print(father_path)
sys.path.append(father_path)

################################
# Local imports
from timetagger4 import TimeTagger as tg
# import timetagger4
import time


class Tagger():
    def __init__(self,index = 0):
        self.index = index
        self.trigger_level = 0
        self.trigger_type = False

        self.channels = [False, False, False, False]
        self.levels = [1,1,1,1]
        self.type = [False,False,False,False]
        self.starts = [0,0,0,0]
        self.stops = [600,600,600,600]

        self.card = None
        self.started = False

        self.init_card()
        print('card initialized 1')


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

    def set_channel_window(self,channel,start=0,stop=600000):
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
        kwargs['index'] = self.index

        if self.card is not None:
            self.stop()

        self.card = tg(**kwargs)

    def start_reading(self):
        #self.init_card()

        self.started = True
        self.card.startReading()
        print('started reading')

    def get_data(self,timeout = 2):
        start = time.time()
        while time.time()-start < timeout:
            status, data = self.card.getPackets()
            # print(status,data)
            if status == 0: # trigger detected, so there is data
                print('trigger detected')
                if data == []:
                    return None
                else:
                    return data

            elif status == 1: # no trigger seen yet, go to sleep for a bit and try again
                time.sleep(0.0001)

            else:
                raise

        return None

    def stop(self):
        if not self.card is None:
            if self.started:
                self.card.stopReading()
                self.started = False
            self.card.stop()
            self.card = None


if __name__ == '__main__':
    tagger = Tagger()
    for i in range(1,4):
        tagger.enable_channel(i)
        tagger.set_channel_level(i,-2.25)
        tagger.set_channel_falling(i)
        tagger.set_channel_window(i,stop = 2*1000*1000)
    tagger.set_trigger_level(-0.5)
    tagger.set_trigger_falling()
    tagger.set_trigger_level(0.5)
    tagger.set_trigger_rising()

    print("Start reading")
    tagger.start_reading()
    while True:
        print("Get data")
        data = tagger.get_data()
        if not data is None:
            for d in data:
                print(d)

        time.sleep(0.01)