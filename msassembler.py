#!/usr/bin/env python3

# Ensamblador para la Máquina Sencilla.
#
# Interpreta los valores decimales como constantes, y los valores precedidos
# por '@' como direcciones.

import sys
import argparse

OPERATIONS = ["ADD", "MOV", "CMP", "BEQ", "IN", "OUT"]
OPERAND_NUMBER = {"ADD": 2, "MOV": 2, "CMP": 2, "BEQ": 1, "IN": 2, "OUT": 2}
LABEL_SEPARATOR = ':'

class Assembler:
    _src_start = 0
    _data_start = 100

    _operations = set(OPERATIONS)
    _opcodes = dict({"ADD": '00',
                     "CMP": '01',
                     "MOV": '10',
                     "BEQ": '11',
                     "IN":  '1110',
                     "OUT": '1111'})
    _operand_number = dict(OPERAND_NUMBER)

    def __init__(self, source, output, verbose=False):
        self._labels = dict()
        self._variables = dict()
        self._constants = dict()
        self._data_pointer = self._data_start


        self._input_file = open(source, 'r')

        self._output_file = sys.stdout if not output else open(output, 'w')

        # Parsing labels:
        self._parseLabels()

        if verbose:
            print("Ensamblando", source, "...")
            print("Origen código: @", self._src_start, sep='')
            print("----------")

        # Assembling:
        self._assemble(self._parseInstructions(), prettyPrint=verbose)

        if verbose:
            print("----------")
            print("\nEtiquetas:")
            for label in sorted(self._labels, key=self._labels.get):
                print('@', self._labels[label], '\t', label, sep='')

            print("\nVariables declaradas (data segment):")
            for v in sorted(self._variables, key=self._variables.get):
                print('@', self._variables[v], '\t', v, sep='')
            print("\nConstantes utilizadas (data segment):")

            for c in sorted(self._constants, key=self._constants.get):
                print('@', self._constants[c], '\t', c, sep='')


    def __del__(self):
        self._input_file.close()
        if self._output_file is not sys.stdout:
            self._output_file.close()

    def _hasLabel(self, line):
        ''' Check if the line contains a label (assuming it is delimited
        by ':').
        '''
        return ':' in line

    def _getLabel(self, line):
        ''' Get the label name, assuming it starts with no leading space, and
        ends with ':'
        '''
        sep = line.find(LABEL_SEPARATOR)
        return line[0:sep].lstrip().lower()

    def _defineLabel(self, label, address):
        if label in self._labels:
            self._abort("Error: label " + label + " has multiple definitions.")
        else:
            self._labels[label] = address

    def _labelDefined(self, label):
        return label in self._labels

    def _getIdLocation(self, identifier):
        '''
        Checks whether the identifier is a known jump point, a variable or a
        constant, and, if it is, returns its location in memory.
        If a variable isn't yet defined, allocates space in the data portion of
        memory.
        '''
        # Label:
        if identifier in self._labels:
            return self._labels[identifier]

        # Constant:
        if identifier.isnumeric():
            if not identifier in self._constants:
                self._constants[identifier] = self._data_pointer
                self._data_pointer += 1
            return self._constants[identifier]

        # Memory address:
        if '@' in identifier:
            address = identifier.replace('@', '')
            return min((2**7)-1, int(address))

        # Variable:
        if not identifier in self._variables:
                self._variables[identifier] = self._data_pointer
                self._data_pointer += 1

        return self._variables[identifier]

    def _getOpcode(self, instruction):
        return self._opcodes[instruction]

    def _parseLabels(self):
        '''
        Scan the file keeping track of each line's address. For each label
        that is defined using ':', save it with its address.
        '''
        current_address = self._src_start

        self._input_file.seek(0)
        for line in self._input_file:
            if (self._hasLabel(line)):
                self._defineLabel(self._getLabel(line), current_address)

            if (line[0] not in ['#', '/']):
                current_address += 1

    def _parseInstructions(self):
        '''
        Scan the file reading valid instructions with its operands.
        Returns a list of tuples (instruction, operand1, [operand0]).
        '''
        res = []
        current_line = 1

        self._input_file.seek(0)
        for line in self._input_file:

            # Stripping comments:
            comment_start = line.find('#')
            if comment_start != -1:
                line = line [:comment_start]
            if len(line) == 0:
                current_line += 1
                continue

            # Skipping leading label:
            if self._hasLabel(line):
                line = line[line.find(LABEL_SEPARATOR)+1:]
                if not len(line): # End of line.
                    current_line += 1
                    continue

            # Cleaning extra white-space:
            line = line.replace("  ", ' ')
            line = line.replace('\t', '')
            line = line.strip()

            line = line.replace(' ', ',')
            tokens = line.split(',')
            tokens = [t for t in tokens if t.isalnum() or '@' in t]


            # Operation:
            operation = tokens[0].upper()
            if operation not in self._operations:
                self._abort("Error: unknown operation in line %d"
                            % current_line)
            if (len(tokens) < self._operand_number[operation] + 1):
                # Syntax: [op, op1, op2]
                self._abort("Error: missing operand/s in %s, line %d"
                            % (operation, current_line))

            # First operand:
            operand1 = tokens[1]

            instruction = []
            instruction.append(operation)
            instruction.append(operand1)

            # Second operand?
            if (len(tokens) > 2):
                operand0 = tokens[2]
                instruction.append(operand0)

            res.append(instruction)
            current_line += 1
        return res

    def _assemble(self, operations, prettyPrint=False):
        '''
        Given a list of tuples of instructions, translates them to their
        binary representation.
        If prettyPrint is enabled, it displays spaces between fields.
        '''

        for o in operations:
            mnemonic = o[0].upper()
            opcode = self._getOpcode(mnemonic)

            if len(o) == 2: # opcode, D
                F_operand = 0
                D_operand = o[1]
            else:           # opcode, F, D
                F_operand = o[1]
                D_operand = o[2]

            # D operand:
            if mnemonic not in ["IN", "OUT"]:
                D = bin(self._getIdLocation(D_operand)) # Variable lookup
            else:
                D = bin(int(D_operand))
            D = D[2:] # Discarding '0b' from the string

            # F operand (if present):
            if F_operand == 0:
                F = bin(0) # Just one operand: D
            elif mnemonic in ["IN", "OUT"]:
                F = bin(int(F_operand)) # Device/offset location
            else:
                F = bin(self._getIdLocation(F_operand))
            F = F[2:]


            # Padding
            D = D.zfill(7)
            F = F.zfill((2 + 7) - len(opcode))

            if prettyPrint:
                print("%-3s\t%4s\t%7s (%3d)\t%7s (%3d)" %
                      (o[0], opcode, F, int(F, 2), D , int(D, 2)))
            else:
                print(opcode, F, D, sep='', file=self._output_file)

    def _abort(self, message):
        print(message)
        exit(-1)


def main():
    parser = argparse.ArgumentParser(description='Ensambla código de la Máquina Sencilla.')
    parser.add_argument('input', help='Archivo a ensamblar', type=str)
    parser.add_argument('-v', '--verbose', help='Mostrar detalles del ensamblado',
                        action='store_true')
    parser.add_argument('-o', '--output', help='Archivo de salida',
                        type=str)
    args = parser.parse_args()

    Assembler(args.input, args.output, args.verbose)

if __name__ == "__main__":
    main()