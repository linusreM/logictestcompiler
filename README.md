
# TTL Logic test compiler

This repo contains a small program to compile test routines for the boards used in labs at KTH in campus Flemingsberg. The boards run a small program that executes on binary data stored on the internal flash. To make authoring tests a bit less of a PITA a small language is used which can be compiled into the binary format using the script in this repo.

## Test routines

The cards are able to preform sequences of logic tests. There are 16 input/output pins that can be controlled in the boards. Tests are constrained to the following structure:
* Selected outputs are set to a designated level.
* wait a moment.
* Selected inputs are read and compared to an asserted value.
* If the value matches the inputs proceed to the next instruction

This continues either until the end of the file or if the asserted comparison fails.
The card indicates success (completed test) with a green light, and failure (input does not match) with a red light.

## Test language

The test language allows a user to specify the test sequence. A typical line could look like this.

`0,1,2,3; 4(0b1100); 8; 1(0)`

The basic structure of one test is as following:

`[selected outputs]; [output values]; [selected inputs]; [asserted value]`

Selected inputs and outputs are one of the numbers 0-15. If multiple should be selected they are separated by commas.

Output and asserted value specify values of the selected bits. Multiple bits can be specified with a single value, or with multiple in sequence. The total number of value bits must correspond with the total number of selected bits. 

Values are specified in the following form:
`[n bits]([bits value])`
values can be specified in any manner that could be evaluated by python into an integer, using any symbols defined in the file.

Valid syntax include: `Binary: 5(0b01001), Hexadecimal: 8(0xA5), Decimal: 7(64)`

Arithmetic is also allowed, so `5(0b101 + 0xA)` would be valid.

If multiple distinct values are needed they are separated by comma.
Ex. `1(0b1), 1(0b0), 2(2)`

Values are mapped to the preceding selected bits in the order they appear. for example `4,5; 2(0b10)` would map 4=>1 and 5=>0.

Symbols can be predefined to substitute integer values as either selected bit or value. Symbols are defined using `[name]=[value]` syntax. The symbols are indexed before the tests are assembled and may appear anywhere in the file. The typical usecase would be to name signals according to some schema.

## Example

A simple test modeling an and gate (outputs: A,B | input: S) could look like this:
<code>
A=0<br>
B=1<br>
S=8<br>
<br>
A,B; 2(0b00); S; 1(0b0)<br>
A,B; 2(1); S; 1(0)<br>
A,B; 2(0x2) ; S; 1(1)</code>

