"""Execute: python3 testar.py. Dados de teste ficam em pastas temporarias."""
import concurrent.futures
import datetime as dt
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from app import Engine, DataLock, build, make_handler, amount_cents, seed_demo


class FinanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = build()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.engine = Engine(self.binary, self.folder)
        self.addCleanup(self.temp.cleanup)

    def add(self, amount="10,00", kind="R", date="2026-11-10", category=1, description="Teste"):
        return self.engine.add(dict(amount=amount, type=kind, date=date, category=category, description=description))

    def state(self, start="2026-11-01", end="2026-11-30"):
        return self.engine.state(start, end)

    def test_01_empty(self):
        s = self.state()
        self.assertEqual([s[k] for k in ("income","expenses","net","balance")], [0,0,0,0])
        self.assertEqual(s["transactions"], [])

    def test_02_persistence_and_exact_cents(self):
        self.add("50,25"); self.add("20.10", "D", category=4)
        self.engine = Engine(self.binary,self.folder)
        s = self.state()
        self.assertEqual((s["income"],s["expenses"],s["net"],s["balance"]),(5025,2010,3015,3015))
        self.assertEqual(s["categories"][3]["expenses"],2010)

    def test_03_period_and_carry_forward(self):
        self.add("100",date="2026-10-31"); self.add("40","D",category=3)
        self.add("20",date="2026-12-01")
        s=self.state(); self.assertEqual((s["net"],s["balance"]),(-4000,6000))
        self.assertEqual(len(s["transactions"]),1)
        with self.assertRaises(ValueError): self.state("2026-12-01","2026-11-01")

    def test_04_negative_balance_is_allowed(self):
        self.add("0,01","D",category=4)
        self.assertEqual(self.state()["balance"],-1)

    def test_05_cancellation_preserves_history(self):
        id=self.add(); self.engine.cancel(id)
        self.assertEqual(len((self.folder/"lancamentos.dat").read_bytes().splitlines()),2)
        self.assertEqual(self.state()["income"],0)
        with self.assertRaises(ValueError): self.engine.cancel(id)
        self.assertEqual(len((self.folder/"lancamentos.dat").read_bytes().splitlines()),2)

    def test_06_invalid_values(self):
        for value in ["","0","-1","+1","abc","1.234",".",".50","10.","1 0","1e2","10000000","1.2.3","1,000.00","NaN"]:
            with self.subTest(value=value), self.assertRaises(ValueError): self.add(value)
        self.assertFalse((self.folder/"lancamentos.dat").exists())
        self.assertEqual(amount_cents("12,5"),1250)

    def test_07_valid_and_invalid_calendar_dates(self):
        self.add(date="2024-02-29")
        for date in ["2025-02-29","2026-04-31","2026-13-01","2026-00-01","1500-01-01","2026-1-1"]:
            with self.subTest(date=date),self.assertRaises(ValueError):self.add(date=date)
        with self.assertRaises(ValueError):self.engine.run("ADD","R","20250229","01","000001000","Teste")

    def test_08_limits_and_utf8(self):
        self.add("9999999.99",description="Alimentação e salário")
        self.add("9999999,99")
        s=self.state();self.assertEqual(s["income"],1999999998)
        self.assertTrue(any(r["description"]=="Alimentação e salário" for r in s["transactions"]))
        with self.assertRaises(ValueError):self.add(description="á"*31)
        with self.assertRaises(ValueError):self.add(description="duas\nlinhas")

    def test_09_invalid_history_is_not_modified(self):
        self.add();file=self.folder/"lancamentos.dat";good=file.read_bytes()
        variants=[b"bad\n",good.replace(b"#",b"!"),good[:26]+b"X"+good[27:],
                  good[:29]+b"abcdefghi"+good[38:],good[:18]+b"20260230"+good[26:],
                  good[:27]+b"00"+good[29:],good[:29]+b"000000000"+good[38:],good+good]
        for bad in variants:
            file.write_bytes(bad)
            with self.assertRaises(RuntimeError):self.state()
            with self.assertRaises(RuntimeError):self.add()
            self.assertEqual(file.read_bytes(),bad)

    def test_10_file_error(self):
        (self.folder/"lancamentos.dat").mkdir()
        with self.assertRaises(RuntimeError):self.add()

    def test_11_serialized_writes(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            ids=list(pool.map(lambda _:self.add("0.01"),range(16)))
        self.assertEqual(len(set(ids)),16)
        self.assertEqual(self.state()["income"],16)

    def test_12_event_capacity(self):
        row=lambda i:f"{i:09}00000000020261110R01000000001{'Teste':60}#\n"
        file=self.folder/"lancamentos.dat";file.write_text("".join(row(i) for i in range(1,10001)))
        self.assertEqual(self.state()["income"],10000)
        before=file.read_bytes()
        with self.assertRaises(ValueError):self.add()
        self.assertEqual(file.read_bytes(),before)

    def test_13_direct_core_validation(self):
        for command in [("INVALID",),("ADD","X","20261110","01","000001000","Teste"),
                        ("ADD","R","20261110","99","000001000","Teste"),
                        ("ADD","R","20261110","01","000000000","Teste")]:
            with self.assertRaises(ValueError):self.engine.run(*command)

    def test_14_demo_does_not_overwrite_existing_data(self):
        self.add();before=(self.folder/"lancamentos.dat").read_bytes();seed_demo(self.engine)
        self.assertEqual((self.folder/"lancamentos.dat").read_bytes(),before)

    def test_15_instance_lock(self):
        first=DataLock(self.folder)
        try:
            with self.assertRaises(RuntimeError):DataLock(self.folder)
        finally:first.file.close()

    def test_16_http_auth_export_backup(self):
        self.add(description="=1+1")
        server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(self.engine,"test-token",False))
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        def request(path,headers=None):
            conn=http.client.HTTPConnection("127.0.0.1",server.server_port)
            conn.request("GET",path,headers=headers or {})
            response=conn.getresponse();result=(response.status,response.read());conn.close();return result
        try:
            self.assertEqual(request("/api/state")[0],403)
            self.assertEqual(request("/api/state",{"X-App-Token":"test-token","Origin":"http://other.example"})[0],403)
            self.assertEqual(request("/",{"Host":"other.example"})[0],403)
            code,csv=request("/api/export?start=2026-11-01&end=2026-11-30",{"X-App-Token":"test-token"})
            self.assertEqual(code,200);self.assertIn(b"'=1+1",csv)
            self.assertEqual(request("/api/backup",{"X-App-Token":"test-token"})[1],(self.folder/"lancamentos.dat").read_bytes())
        finally:server.shutdown();server.server_close();worker.join()


if __name__ == "__main__":unittest.main(verbosity=2)
