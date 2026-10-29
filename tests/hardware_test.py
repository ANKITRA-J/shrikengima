"""Exercise the real USB/MCU/FPGA path; requires flashed Enigma hardware."""
import argparse
import itertools
import random
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'desktop'), str(ROOT/'reference')]
from serial_manager import SerialManager
from enigma_ref import Enigma, ROTOR_ORDER

def require(result):
    ok, value = result
    if not ok:
        raise AssertionError(value)
    return value

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    parser.add_argument('--stress-rounds', type=int, default=0, help='Extra pairs of randomized 512-letter encrypt/decrypt messages')
    args = parser.parse_args()
    client = SerialManager()
    print(require(client.connect(args.port)), flush=True)
    rng = random.Random(1941)
    try:
        print("Self-test:", require(client.selftest()), flush=True)
        for order in itertools.permutations(range(5), 3):
            windows = [rng.randrange(26) for _ in range(3)]
            rings = [rng.randrange(26) for _ in range(3)]
            plugs = ['AZ', 'BY', 'CX']
            require(client.configure(order, windows, rings, plugs))
            oracle = Enigma([ROTOR_ORDER[i] for i in order], ''.join(chr(65+i) for i in windows), ''.join(chr(65+i) for i in rings), plugs)
            message = 'Hello, FPGA! 0123456789\n' + ''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=24))
            expected = oracle.text(message)
            response = require(client.encrypt(message))
            assert response['result'] == expected, order
            assert response['final_positions'] == oracle.window(), order
            assert require(client.decrypt(expected))['result'] == message.upper(), order
        print("PASS: all 60 rotor orders and reciprocal processing", flush=True)
        require(client.reset())
        for message in ['', '123 !\t\r\n', 'A'*512]:
            assert require(client.encrypt(message))['result'] == Enigma().text(message)
        for message in ['é', 'A'*513, 'A\x00']:
            assert not client.encrypt(message)[0]
        require(client.reset())
        assert require(client.encrypt('AAAAA'))['result'] == 'BDZGO'
        require(client.reset())
        for round_no in range(args.stress_rounds):
            order = rng.sample(range(5), 3)
            windows = [rng.randrange(26) for _ in range(3)]
            rings = [rng.randrange(26) for _ in range(3)]
            plugs = ['AZ', 'BY', 'CX']
            require(client.configure(order, windows, rings, plugs))
            oracle = Enigma([ROTOR_ORDER[i] for i in order], ''.join(chr(65+i) for i in windows), ''.join(chr(65+i) for i in rings), plugs)
            message = ''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=512))
            expected = oracle.text(message)
            response = require(client.encrypt(message))
            assert response['result'] == expected, ('stress encrypt', round_no)
            assert response['final_positions'] == oracle.window(), ('stress positions', round_no)
            assert require(client.decrypt(expected))['result'] == message, ('stress decrypt', round_no)
            if (round_no + 1) % 5 == 0:
                print(f'PASS: {round_no + 1} stress rounds / {(round_no + 1) * 1024} extra FPGA letters', flush=True)
        require(client.reset())
        print('PASS: hardware self-test, all 60 rotor orders, rings, plugs, reciprocal processing, 512-byte boundary, validation, reset')
    finally:
        client.disconnect()
if __name__ == '__main__':
    main()
