import serial
import time


class RFGenerator():
	def __init__(self, port = 'COM5'):
		self.ser = serial.Serial(port=port, baudrate=115200, timeout  = 0.2)

	def set_freq(self, freq):
		if float(freq) < 20:
			print('freq too low')
		if float(freq) > 9800:
			print('freq too high')
		self.write('FREQ:CW {}MHz'.format(round(freq,4)))

	def get_freq(self):
		self.write('FREQ:CW?')
		return round(float(self.ser.readline().decode('utf-8').strip('HZ\r\n'))/10**6,4)

	def set_power(self, power):
		self.write('POWER {}'.format(power))

	def set_vernier(self, vernier):
		self.write('VERNIER {}'.format(vernier))

	def toggle_buzzer(self, state = 'OFF'):
		self.write('*BUZZER {}'.format(state))

	def define_sweep_list(self, sweep):
		self.write('ABORT')
		self.write('LIST:CLEAR')
		for s in sweep:
			self.write('LIST:ADD {}MHz'.format(s))

	def start_sweep(self,dwell=1000,step=True,cont=False):
		self.write('SWE:MODE LIST')

		if cont:
			self.write('INIT:CONT 1')
		else:
			self.write('INIT:CONT 0')

		if step:
			self.write('TRIG:STEP')
		else:
			self.write('TRIG:SWEEP')

		self.write('SWE:DWELL {}'.format(dwell))

		self.write('INIT:IMM')

	def stop_sweep(self):
		self.write('ABORT')

	def toggle_state(self, state):
		if state:
			self.write('OUTP:STAT ON')
		else:
			self.write('OUTP:STAT OFF')

	def get_state(self):
		self.write('OUTP:STAT?')
		state = self.ser.readline().decode('utf-8').strip('\r\n')
		return state == 'ON'

	def wrap_message(self, mes):
		mes += '\n'
		return bytes(mes, 'utf-8')

	def write(self, mes):
		self.ser.write(self.wrap_message(mes))

	def reset(self):
		self.write('*RST')

	def close(self):
		self.ser.close()

if __name__ == '__main__':
	rf = RFGenerator()
	# rf.reset()
	rf.toggle_buzzer(state = 'OFF')
	# rf.set_freq('432')
	# rf.set_power('5')
	# rf.set_vernier('0.9')
	# rf.define_sweep_list([100,200,300,400,500])
	# rf.start_sweep(dwell=0.2,cont=False,step=False)


	i = 0
	while True:
		start = time.time()
		rf.set_freq(20 + (i/20)%6480)
		i+=1
		time.sleep(0.001)

	rf.close()
