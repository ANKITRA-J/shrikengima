"""Regenerate the standalone source consumed by Go Configure."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'fpga/rtl'
MODULES = ['enigma_top', 'enigma_core', 'rotor_rom', 'packet_wrapper', 'crc8', 'uart_rx', 'uart_tx', 'led_controller']
def main():
    sources = []
    for name in MODULES:
        source = (RTL / (name + '.v')).read_text()
        source = source.replace('`include "helpers.v"', (RTL / 'helpers.v').read_text())
        sources.append(source)
    target = ROOT / 'fpga/project/enigma/ffpga/src/main.v'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('// Generated from fpga/rtl by tools/prepare_fpga.py.\n' + '\n'.join(sources))
    print(target)
if __name__ == '__main__':
    main()
