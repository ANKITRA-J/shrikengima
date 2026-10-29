"""Run reproducible host tests and RTL simulation (requires Verilator + C++)."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
def run(args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verilator', default='verilator')
    parser.add_argument('--runtime', type=Path, help='Runtime include directory for vendor distributions without make support')
    parser.add_argument('--build', type=Path, default=ROOT/'build/checks')
    args = parser.parse_args()
    build = args.build.resolve(); build.mkdir(parents=True, exist_ok=True)
    run([sys.executable, ROOT/'reference/enigma_ref.py'])
    run([sys.executable, '-m', 'unittest', 'discover', '-s', ROOT/'tests', '-p', 'test_desktop.py'])
    native = build/'test-uart'
    run(['c++', '-std=c++17', '-I'+str(ROOT/'tests/native'), '-I'+str(ROOT/'firmware/enigma_shrike'), ROOT/'tests/native/test_uart.cpp', ROOT/'firmware/enigma_shrike/uart_protocol.cpp', '-o', native])
    run([native])
    with (build/'packet_vectors.hex').open('w') as out:
        run([sys.executable, ROOT/'tests/generate_packet_vectors.py'], stdout=out)
    for top in ['enigma_core_tb', 'packet_wrapper_tb', 'enigma_top_tb']:
        obj = build/top
        rtl = [p for p in (ROOT/'fpga/rtl').glob('*.v') if p.name!='helpers.v']
        cmd = [args.verilator, '--timing', '-Wno-fatal', '--top-module', top,
               '-I'+str(ROOT/'fpga/rtl'), '--Mdir', obj, ROOT/'fpga/sim'/f'{top}.v', *rtl]
        if args.runtime:
            run(cmd+['--cc', '--main'])
            runtime = args.runtime.resolve()
            run(['c++', '-std=c++20', '-DVL_TIME_CONTEXT', '-O0', '-pthread', '-I'+str(runtime), '-I'+str(obj), *obj.glob('*.cpp'), *[runtime/f for f in ('verilated.cpp','verilated_threads.cpp','verilated_timing.cpp')], '-o', obj/'test'])
            run([obj/'test'], cwd=build)
        else:
            run(cmd+['--binary', '-j', '4'])
            run([obj/f'V{top}'], cwd=build)
if __name__ == '__main__':
    main()
