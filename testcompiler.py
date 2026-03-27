from dataclasses import dataclass, field
import sys
import re

class DigiboardTest:

    @dataclass
    class TestLine:
        text_line: str = ""
        line_no: int = 0
        is_step: bool = False
        is_valid: bool = False
        is_evaluated: bool = False
        signals_out: list[int] = field(default_factory=list)
        out_value: list[bool] = field(default_factory=list)
        signals_in: list[int] = field(default_factory=list)
        in_value: list[bool] = field(default_factory=list)

    def __init__(self, name, input_text=None):
        self.test = []
        self.symbols = {}
        self.name = name
        if input_text is not None:
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
                    line.is_valid = True
                    line.is_evaluated = True
                except:
                    line.is_valid = False
                    line.is_evaluated = True
                    print("Symbol in:{line_text} - at line:{line_no} was not able to be parsed".format(line_text=line.text_line, line_no=line.line_no))

        for line in self.test:
            if not line.is_evaluated:
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
                    line.is_valid = False
                    line.is_evaluated = True
                    continue
                try:
                    line.out_value = self.get_values(out_values)
                    line.in_value = self.get_values(in_values)
                except Exception as e:
                    print("Error: {e} Values in:{line_text} - at line:{line_no} was not able to be evaluated".format(e=e, line_text=line.text_line, line_no=line.line_no))
                    line.is_valid = False
                    line.is_evaluated = True
                    continue
                line.is_valid = True
                line.is_evaluated = True
                line.is_step = True

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
            if not line.is_valid:
                raise Exception("Not all lines are valid, cannot output binary.")
            if line.is_step:
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
                binary.extend([output_bytes & 0xff, (output_bytes >> 8) & 0xff,
                               output_mask & 0xff,  (output_mask >> 8) & 0xff,
                               input_bytes & 0xff,  (input_bytes >> 8) & 0xff,
                               input_mask & 0xff, (input_mask >> 8) & 0xff])
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
            with open(filename, encoding='utf-8') as fd:
                test = fd.read()
        except:
            print("Cannot open file " + sys.argv[1])
            return
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
