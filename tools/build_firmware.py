"""Build ESP32-S3 firmware/LittleFS; optionally flash the explicitly named port."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
FQBN = 'esp32:esp32:esp32s3:CDCOnBoot=cdc,FlashSize=8M,PartitionScheme=default_8MB'
def run(args):
    try:
        subprocess.run([str(a) for a in args], check=True)
    except FileNotFoundError as exc:
        raise SystemExit(f'Cannot run {args[0]}; install the tool or pass its path explicitly') from exc
def default_arduino_cli():
    installed = shutil.which('arduino-cli')
    if installed:
        return installed
    bundled = Path('/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli')
    if sys.platform == 'darwin' and bundled.is_file():
        return str(bundled)
    return 'arduino-cli'
def default_esp32_tools():
    if sys.platform == 'darwin':
        data = Path.home()/'Library/Arduino15'
    elif sys.platform == 'win32':
        data = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData/Local')))/'Arduino15'
    else:
        data = Path.home()/'.arduino15'
    return data/'packages/esp32/tools'
def tool(root, name):
    # Arduino package tools have a version directory, with .exe on Windows.
    filename = name + ('.exe' if sys.platform == 'win32' else '')
    choices = [path for path in root.glob(f'*/{filename}') if path.is_file()]
    if not choices:
        raise SystemExit(f'Cannot find {name} under {root}; install ESP32 Arduino core 3.3.12')
    # Numeric ordering avoids choosing 5.9 over 5.10 when several are installed.
    return max(choices, key=lambda path: tuple(int(n) for n in re.findall(r'\d+', path.parent.name)))
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--arduino-cli', default=default_arduino_cli(), help='Arduino CLI executable (PATH or bundled macOS Arduino IDE by default)')
    p.add_argument('--esp32-tools', type=Path, default=default_esp32_tools(), help='Arduino packages/esp32/tools directory (platform default unless overridden)')
    p.add_argument('--libraries', type=Path)
    p.add_argument('--build', type=Path, default=ROOT/'build/firmware')
    p.add_argument('--bitstream', type=Path, required=True, help='Vendor FPGA_bitstream_MCU.bin (MCU SPI format), not raw core, FLASH_MEM, OTP or XML')
    p.add_argument('--port', help='Flash only when this option is supplied; board must have 8 MB flash')
    a = p.parse_args()
    image = a.bitstream.read_bytes()
    if len(image) < 1024:
        raise SystemExit('Refusing empty/placeholder FPGA image')
    build = a.build.resolve(); build.mkdir(parents=True, exist_ok=True)
    cmd = [a.arduino_cli,'compile','--fqbn',FQBN,'--build-path',build,ROOT/'firmware/enigma_shrike']
    if a.libraries: cmd += ['--libraries',a.libraries.resolve()]
    run(cmd)
    # Arduino CLI can clear the build directory when options/libraries change.
    # Populate filesystem input only after compilation has completed.
    data = build/'littlefs-data'; data.mkdir(exist_ok=True)
    (data/'fpga_bitstream.bin').write_bytes(image)
    partition = next(line.split(',') for line in (build/'partitions.csv').read_text().splitlines() if line.startswith('spiffs,'))
    offset,size = int(partition[3].strip(),0),int(partition[4].strip(),0)
    fs = build/'littlefs.bin'
    run([tool(a.esp32_tools/'mklittlefs','mklittlefs'),'-c',data,'-b','4096','-p','256','-s',size,fs])
    print(f'Built firmware and filesystem in {build}; filesystem offset {offset:#x}, size {size:#x}')
    if a.port:
        esptool = tool(a.esp32_tools/'esptool_py','esptool')
        run([esptool,'--chip','esp32s3','--port',a.port,'--baud','460800','write-flash',
             '0x0',build/'enigma_shrike.ino.bootloader.bin','0x8000',build/'enigma_shrike.ino.partitions.bin',
             '0xe000',build/'boot_app0.bin','0x10000',build/'enigma_shrike.ino.bin',hex(offset),fs])
if __name__ == '__main__':
    main()
