"""Exercise real GUI buttons and worker callbacks against a connected FPGA board.

Run after hardware_test.py. Set QT_QPA_PLATFORM=offscreen for unattended use.
"""
import argparse
import sys
import tempfile
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'desktop'))
from PySide6.QtWidgets import QApplication, QMessageBox
from main_window import MainWindow
from enigma_model import EnigmaModel
from serial_manager import SerialManager
from settings_manager import SettingsManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    args = parser.parse_args()
    app = QApplication([])
    errors = []
    QMessageBox.critical = lambda parent, title, text: errors.append((title, text))
    QMessageBox.warning = lambda parent, title, text: errors.append((title, text))
    with tempfile.TemporaryDirectory() as temp:
        window = MainWindow(EnigmaModel(), SerialManager(), SettingsManager(str(Path(temp)/'settings.json')))
        window.show()
        def click(button):
            assert button.isEnabled(), button.text()
            button.click()
            deadline = time.monotonic() + 60
            while window.job is not None and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)
            assert window.job is None, 'GUI worker timed out'
            app.processEvents()
            assert not errors, errors
        try:
            index = window.port_combo.findData(args.port)
            assert index >= 0, 'Requested board port is not listed'
            window.port_combo.setCurrentIndex(index)
            click(window.connect_btn)
            assert window.serial.is_connected()
            window.input_text.setPlainText('HELLOWORLD')
            click(window.encrypt_btn)
            assert window.output_text.toPlainText() == 'ILBDAAMTAZ'
            assert window.window_right_combo.currentIndex() == 0, 'Initial position changed'
            window.input_text.setPlainText(window.output_text.toPlainText())
            click(window.decrypt_btn)
            assert window.output_text.toPlainText() == 'HELLOWORLD'
            click(window.reset_btn)
            assert window.serial.get_status()[0]
            print('PASS: GUI connect, threaded FPGA encrypt/decrypt, retained initial windows and reset', flush=True)
        finally:
            if window.job is not None:
                window.job.wait(60000)
                app.processEvents()
            window.close()


if __name__ == '__main__':
    main()
