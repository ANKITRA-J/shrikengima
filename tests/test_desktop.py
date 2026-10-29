import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from serial_manager import SerialManager
from enigma_model import EnigmaModel

class Port:
    is_open=True
    def __init__(self,replies): self.replies=replies;self.data=bytearray();self.sent=[]
    def write(self,wire):
        request=json.loads(wire);self.sent.append(request)
        for response in self.replies(request): self.data.extend(json.dumps(response).encode()+b'\n')
        return len(wire)
    def read(self,n):
        b=self.data[:n];del self.data[:n];return bytes(b)
    def close(self):self.is_open=False

class DesktopTests(unittest.TestCase):
    def client(self,replies):
        client=SerialManager();client.port=Port(replies);return client
    def test_preserve_text(self):
        self.assertEqual(EnigmaModel.normalize_message('hello, 123!\n'),'hello, 123!\n')
        self.assertEqual(EnigmaModel.normalize_message(''),'')
        for text in ['Aé','A\x00','A'*513]:
            with self.assertRaises(ValueError):EnigmaModel.normalize_message(text)
    def test_ascii_plugs(self):
        model=EnigmaModel();self.assertFalse(model.add_plugboard_pair('é','A')[0])
        self.assertTrue(model.add_plugboard_pair('A','B')[0]);self.assertFalse(model.add_plugboard_pair('B','C')[0])
    def test_clear_plugs_explicit(self):
        c=self.client(lambda req:[dict(id=req['id'],ok=True)])
        self.assertTrue(c.configure([0,1,2],[0,0,0],[0,0,0],[])[0])
        self.assertEqual(c.port.sent[0]['plugs'],[])
        self.assertEqual(c.port.sent[0]['positions'],'AAA')
    def test_stale_reply_and_final_position(self):
        c=self.client(lambda req:[dict(id=65535,ok=True,result='BAD'),dict(id=req['id'],ok=True,result='BDZGO',engine='fpga_enigma',final_positions='AAF')])
        ok,r=c.encrypt('AAAAA');self.assertTrue(ok);self.assertEqual(r['windows'],[0,0,5]);self.assertEqual(r['result'],'BDZGO')
    def test_missing_success_rejected(self):
        c=self.client(lambda req:[dict(id=req['id'],result='')]);self.assertFalse(c.ping()[0]);self.assertFalse(c.is_connected())
    def test_error_never_becomes_ciphertext(self):
        c=self.client(lambda req:[dict(id=req['id'],ok=False,error={'code':'NOT_READY','message':'FPGA unavailable'})])
        ok,r=c.encrypt('AAAAA');self.assertFalse(ok);self.assertNotIn('result',r)
    def test_bad_engine(self):
        c=self.client(lambda req:[dict(id=req['id'],ok=True,result='BDZGO',engine='software')]);self.assertFalse(c.encrypt('AAAAA')[0])

if __name__=='__main__':unittest.main()
