"""Development oracle for Enigma I. Not a desktop processing backend."""
from itertools import permutations
import random

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ROTOR_ORDER = ("I", "II", "III", "IV", "V")
ROTORS = {
    "I": ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II": ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV": ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V": ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
}
REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"

def letters(value, length):
    if not isinstance(value, str) or len(value) != length:
        raise ValueError("incorrect setting length")
    if any(c not in ALPHABET + ALPHABET.lower() for c in value):
        raise ValueError("settings must contain ASCII letters")
    value = value.upper()
    return [ord(c) - 65 for c in value]

def normalize(text):
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if any(not (32 <= ord(c) <= 126 or c in "\t\n\r") for c in text):
        raise ValueError("unsupported character")
    return text.upper()

class Enigma:
    def __init__(self, rotors=("I", "II", "III"),
                 pos="AAA", ring="AAA", plugs=()):
        if (len(rotors) != 3 or any(r not in ROTORS for r in rotors)
                or len(set(rotors)) != 3):
            raise ValueError("select three distinct rotors I through V")
        self.pos, self.ring = letters(pos, 3), letters(ring, 3)
        self.fw = [[ord(c) - 65 for c in ROTORS[r][0]] for r in rotors]
        self.bw = []
        for wiring in self.fw:
            inverse = [0] * 26
            for i, output in enumerate(wiring):
                inverse[output] = i
            self.bw.append(inverse)
        self.notch = [ord(ROTORS[r][1]) - 65 for r in rotors]
        self.ref = [ord(c) - 65 for c in REFLECTOR_B]
        if not isinstance(plugs, (list, tuple)) or len(plugs) > 13:
            raise ValueError("plugboard must be a list of at most 13 pairs")
        self.plug, used = list(range(26)), set()
        for pair in plugs:
            a, b = letters(pair, 2)
            if a == b or a in used or b in used:
                raise ValueError("plugboard pairs must be disjoint")
            used.update((a, b))
            self.plug[a], self.plug[b] = b, a

    def step(self):
        middle = self.pos[1] == self.notch[1]
        right = self.pos[2] == self.notch[2]
        if middle:
            self.pos[0] = (self.pos[0] + 1) % 26
        if middle or right:
            self.pos[1] = (self.pos[1] + 1) % 26
        self.pos[2] = (self.pos[2] + 1) % 26

    def _pass(self, contact, slot, table):
        shift = self.pos[slot] - self.ring[slot]
        return (table[slot][(contact + shift) % 26] - shift) % 26

    def letter(self, ch):
        if not isinstance(ch, str) or len(ch) != 1 or ch not in ALPHABET:
            raise ValueError("letter must be one uppercase ASCII letter")
        self.step()
        contact = self.plug[ord(ch) - 65]
        for slot in (2, 1, 0):
            contact = self._pass(contact, slot, self.fw)
        contact = self.ref[contact]
        for slot in (0, 1, 2):
            contact = self._pass(contact, slot, self.bw)
        return chr(self.plug[contact] + 65)

    def text(self, text):
        text = normalize(text)  # validate the whole message before stepping
        return "".join(self.letter(c) if c in ALPHABET else c for c in text)

    def window(self):
        return "".join(chr(p + 65) for p in self.pos)


def selftest():
    assert Enigma().text("AAAAA") == "BDZGO"
    assert Enigma().text("BDZGO") == "AAAAA"
    assert Enigma().text("HELLOWORLD") == "ILBDAAMTAZ"
    machine = Enigma(pos="ADU")
    windows = []
    for _ in range(4):
        machine.letter("A")
        windows.append(machine.window())
    assert windows == ["ADV", "AEW", "BFX", "BFY"]
    machine = Enigma()
    assert machine.text(" \t123!?\n") == " \t123!?\n"
    assert machine.window() == "AAA"
    assert Enigma().text("aaaaa") == "BDZGO"
    rng = random.Random(1941)
    for order in permutations(ROTOR_ORDER, 3):
        pos = "".join(rng.choices(ALPHABET, k=3))
        ring = "".join(rng.choices(ALPHABET, k=3))
        message = "".join(rng.choices(ALPHABET + " !123", k=100))
        settings = dict(rotors=order, pos=pos, ring=ring,
                        plugs=("AB", "CD", "EF", "GH"))
        cipher = Enigma(**settings).text(message)
        assert Enigma(**settings).text(cipher) == message
    for plugs in (("AA",), ("AB", "AC"), ("AB", "BA"), ("A1",)):
        try:
            Enigma(plugs=plugs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid plugs accepted")
    machine = Enigma()
    try:
        machine.text("A\u00e9")
    except ValueError:
        assert machine.window() == "AAA"
    else:
        raise AssertionError("non ASCII message accepted")
    for wiring, _ in ROTORS.values():
        assert sorted(wiring) == list(ALPHABET)
    for i, ch in enumerate(REFLECTOR_B):
        j = ord(ch) - 65
        assert j != i and ord(REFLECTOR_B[j]) - 65 == i
    print("Reference checks passed for all 60 rotor orders")

if __name__ == "__main__":
    selftest()
