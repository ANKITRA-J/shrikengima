"""Print hex vectors: 60 orders, each 9 config bytes and 12 five-byte cases."""
import itertools
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reference'))
from enigma_ref import Enigma, ROTOR_ORDER
rng = random.Random(1941)
for order in itertools.permutations(ROTOR_ORDER, 3):
    pos = ''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
    ring = ''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
    machine = Enigma(rotors=order, pos=pos, ring=ring)
    values = [ROTOR_ORDER.index(r) for r in order] + [ord(c)-65 for c in pos+ring]
    for letter in rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=12):
        output = machine.letter(letter)
        values += [ord(c)-65 for c in letter + output + machine.window()]
    for value in values:
        print(f'{value:02x}')
