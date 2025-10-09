#Format: (Bytes) [Stimulus Low]       , [Stimulus High]       , 
#				 [Sensitivity Low]    , [Sensitivity High]    , 
#				 [Expected output Low], [Expected output High],
#				 [Sensitivity Low]    , [Sensitivity High]
#                    ..... Repeat as many as needed .....
#		  (EOF)  [0x00], [0x00], [0x00], [0x00], [0x00], [0x00], [0x00], [0x00]
#		(0x00 * 8)
#
#
#	- Stimulus is the output state of the I/O modules at the start of the test.
#	- Sensitivity sets which of the outputs should be effected by the state setting
#	- Expected output is the expected state that will be presented on the I/O module.
#	- Sensitivity refers to the inputs that should effect evaluation 
#
#	The test ends with eight consecutive bytes of zeroes.
#
#	If a test needs to do a "no op" just make the sensitivity bytes 0x00, and the stimulus non-zero
#
#   File extension is .secret, and name the test according to lab and level, i.e. 1A.secret, 2A.secret, 1B.secret



# add_test("1234", "b0011", "01234567", "b0001101000")
#Outputs Outval Inputs  Inval
#1,2,3,4;4b0001;8-12,14;3d2,3b101
#r;4b0010;


from dataclasses import dataclass, field
import sys
import re

def command(s):
	s.remove(" ", "")
	c = s.split(';')
	out_values = []
	in_values = []
	outputs = [int(a) for a in c[0].split(",")]
	inputs = [int(a) for a in c[2].split(",")]
	for values in c[1].split(","):
		match values[1]:
			case 'b':
				for b in values[1][2:]:
					out_values.append(int(b))
			case 'd':
				for b in range(int(values[0])):
					out_values.append((int(values[2:], 10) >> b) & 1)
			case 'h': 
				for b in range(int(values[0])):
					out_values.append((int(values[2:], 16) >> b) & 1)
	return test


class DigiboardTest:

	@dataclass
	class TestLine:
		text_line: str = ""
		line_no: int = 0
		isStep: bool = False
		isValid: bool = False
		isEvaluated: bool = False
		signals_out: list[int] = field(default_factory=list)
		out_value: list[bool] = field(default_factory=list)
		signals_in: list[int] = field(default_factory=list)
		in_value: list[bool] = field(default_factory=list)

	def __init__(self, name, input_text=None):
		self.test: list[TestLine] = []
		self.symbols = {}
		self.name = name
		if input_text != None:
			self.append_test(input_text)

	def add_test_symbol(self, symbol, value):
		self.symbols[symbol] = value

	def append_test(self, input_text):
		input_text = input_text.splitlines()
		
		line_no = 1
		for text in input_text:
			print(text)
			text = text.split("//")[0]
			text = text.replace(" ", "").replace("\t", "")
			if text != "":
				self.test.append(self.TestLine(text_line=text, line_no=line_no))
			line_no += 1

		#Extract symbols
		for line in self.test:
			if "=" in line.text_line:
				try:
					self.symbols[line.text_line.split("=")[0]] = int(line.text_line.split("=")[1])
					#TODO: Probably would be wise to do some sanity checking here
					line.isValid = True
					line.isEvaluated = True
				except:
					line.isValid = False
					line.isEvaluated = True
					print("Symbol in:{line_text} - at line:{line_no} was not able to be parsed".format(line_text=line.text_line, line_no=line.line_no))
		
		for line in self.test:
			if not line.isEvaluated:
				sections = line.text_line.split(";")
				out_signals = sections[0].split(",")
				in_signals = sections[2].split(",")
				out_values = sections[1].split(",")
				in_values = sections[3].split(",")
				try:
					line.signals_out = self.get_signals(out_signals)
					line.signals_in = self.get_signals(in_signals)
				except Exception as e:
					print("Error: {e}. Signals in:{line_text} - at line:{line_no} was not able to be evaluated".format(e=e, line_text=line.text_line, line_no=line.line_no))
					line.isValid = False
					line.isEvaluated = True
					continue
				try:
					line.out_value = self.get_values(out_values)
					line.in_value = self.get_values(in_values)
				except Exception as e:
					print("Error: {e} Values in:{line_text} - at line:{line_no} was not able to be evaluated".format(e=e, line_text=line.text_line, line_no=line.line_no))
					line.isValid = False
					line.isEvaluated = True
					continue
				line.isValid = True
				line.isEvaluated = True
				line.isStep = True

	def get_signals(self, text):
		signal_list = []
		for s in text:
			signal_list.append(int(eval(s, locals=self.symbols)))
		return signal_list

	def get_values(self, text):
		values_list = []
		for value in text:
			res = re.split(r"\b(1[0-5]|[0-9])\((.*)\)", value)
			digit = int(eval(res[2], locals=self.symbols))
			for i in reversed(range(int(res[1]))): #Number of bits
				values_list.append((digit >> i) & 1)
		return values_list
			
	def compile_binary(self):
		binary = bytearray()
		for line in self.test:
			if not line.isValid:
					raise Exception("Not all lines are valid, cannot output binary.")
			if line.isStep:
				output_bytes = 0
				input_bytes = 0
				output_mask = 0
				input_mask = 0
				for signal, value in zip(line.signals_out, line.out_value):
					output_mask = output_mask | (1 << signal)
					output_bytes = output_bytes | (value << signal)
				for signal, value in zip(line.signals_in, line.in_value):
					input_mask = input_mask | (1 << signal)
					input_bytes = input_bytes | (value << signal)
				binary.extend([output_bytes & 0xff, (output_bytes >> 8) & 0xff, output_mask & 0xff, (output_mask >> 8) & 0xff, input_bytes & 0xff, (input_bytes >> 8) & 0xff, input_mask & 0xff, (input_mask >> 8) & 0xff])
		for i in range(len(binary)):
			binary[i] = self.byteflip(binary[i])
		binary.extend([0,0,0,0,0,0,0,0])
		return binary

	def byteflip(self, b):
		r = 0
		r = r | ((b & 0x80) >> 7)
		r = r | ((b & 0x40) >> 5)
		r = r | ((b & 0x20) >> 3)
		r = r | ((b & 0x10) >> 1)
		r = r | ((b & 0x08) << 1)
		r = r | ((b & 0x04) << 3)
		r = r | ((b & 0x02) << 5)
		r = r | ((b & 0x01) << 7)
		return r

def main():
	if len(sys.argv) > 2:
		filename = sys.argv[1]
		try:
			with open(filename) as fd:
				test = fd.read()
		except:
			print("Cannot open file " + sys.argv[1])
	else:
		print("Missing argument. Usage: python testcompiler.py [input file] [output file]")
		return

	dt = DigiboardTest(sys.argv[2], test)
	try:
		with open(dt.name, "wb") as fd:
			fd.write(dt.compile_binary())
	except:
		print("Cannot write to file " + dt.name)

if __name__ == '__main__':
	main()