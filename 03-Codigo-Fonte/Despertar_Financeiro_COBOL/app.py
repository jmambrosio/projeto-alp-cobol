"""Interface local para o motor COBOL. Python 3.9+, biblioteca padrao."""
import argparse
import calendar
import csv
import datetime as dt
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
CATEGORIES = ["Salário", "Renda extra", "Moradia", "Alimentação", "Transporte",
              "Saúde", "Educação", "Lazer", "Contas da casa", "Compras",
              "Outras receitas", "Outras despesas"]


def build():
    override = os.environ.get("FINANCAS_BIN")
    if override:
        target = Path(override).resolve()
        if not target.is_file():
            raise RuntimeError("Executável informado em FINANCAS_BIN não encontrado.")
        return target
    compiler = shutil.which("cobc")
    if not compiler:
        raise RuntimeError("GnuCOBOL não encontrado. Instale e confira: cobc -V. Consulte o README.")
    folder = ROOT / "build"
    folder.mkdir(exist_ok=True)
    target = folder / ("financas.exe" if os.name == "nt" else "financas")
    source = ROOT / "financas.cob"
    if not target.exists() or source.stat().st_mtime > target.stat().st_mtime:
        result = subprocess.run([compiler, "-x", "-free", "-Wall", "-debug",
                                 "-o", str(target), str(source)], capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return target


class DataLock:
    """Trava do SO mantida durante toda a vida da aplicação, liberada ao encerrar."""
    def __init__(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        self.file = (folder / ".app.lock").open("a+b")
        self.file.seek(0)
        self.file.write(b"0")
        self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError("Esta pasta de dados já está aberta em outra instância.")


def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Informe uma data válida.")
    day = dt.date.fromisoformat(value)
    if day.year < 1601:
        raise ValueError("Use uma data a partir de 1601.")
    return day.strftime("%Y%m%d")


def amount_cents(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,7}(?:[.,][0-9]{1,2})?", value.strip()):
        raise ValueError("Use um valor como 150,50, sem separador de milhar.")
    parts = value.strip().replace(",", ".").split(".")
    cents = int(parts[0]) * 100 + int((parts[1] if len(parts) == 2 else "").ljust(2, "0"))
    if not 1 <= cents <= 999999999:
        raise ValueError("O valor deve estar entre R$ 0,01 e R$ 9.999.999,99.")
    return cents


class Engine:
    def __init__(self, binary, folder):
        self.binary = Path(binary).resolve()
        self.folder = Path(folder).resolve()
        self.folder.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def run(self, *lines):
        payload = "\n".join(map(str, lines)) + "\n"
        with self.lock:
            try:
                result = subprocess.run([str(self.binary)], input=payload.encode("utf-8"),
                    cwd=self.folder, capture_output=True, timeout=15)
            except subprocess.TimeoutExpired:
                raise RuntimeError("A operação excedeu o tempo. Confira o histórico antes de tentar novamente.")
        text = result.stdout.decode("utf-8", errors="strict")
        if result.returncode:
            message = next((line[6:] for line in text.splitlines() if line.startswith("ERROR|")),
                           "Não foi possível executar o motor COBOL.")
            if result.returncode == 2:
                raise ValueError(message)
            raise RuntimeError(message)
        return result.stdout.splitlines()

    def add(self, data):
        kind = data.get("type")
        if kind not in ("R", "D"):
            raise ValueError("Selecione receita ou despesa.")
        date = valid_date(data.get("date"))
        category = data.get("category")
        if type(category) is not int or not 1 <= category <= len(CATEGORIES):
            raise ValueError("Selecione uma categoria válida.")
        description = data.get("description")
        if not isinstance(description, str):
            raise ValueError("Informe uma descrição.")
        description = description.strip()
        if not description or len(description.encode("utf-8")) > 60 or any(ord(c) < 32 or ord(c) == 127 for c in description):
            raise ValueError("Descrição: use de 1 a 60 bytes, sem quebras de linha. Acentos ocupam mais de um byte.")
        cents = amount_cents(data.get("amount"))
        output = self.run("ADD", kind, date, f"{category:02}", f"{cents:09}", description)
        return int(output[-1].split(b"|")[1])

    def cancel(self, identifier):
        if type(identifier) is not int or not 1 <= identifier <= 10000:
            raise ValueError("Identificador inválido.")
        self.run("CANCEL", f"{identifier:09}", dt.date.today().strftime("%Y%m%d"))

    def state(self, start, end):
        output = self.run("LIST", valid_date(start), valid_date(end))
        data = {"transactions": [], "categories": [], "start": start, "end": end}
        for line in output:
            if line.startswith(b"ROW|"):
                row = line[4:]
                date = row[18:26].decode("ascii")
                data["transactions"].append({"id": int(row[:9]), "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                    "type": row[26:27].decode("ascii"), "category": int(row[27:29]),
                    "cents": int(row[29:38]), "description": row[38:98].decode("utf-8").rstrip()})
            elif line.startswith(b"TOTAL|"):
                values = list(map(int, line.split(b"|")[1:]))
                data.update(zip(("income", "expenses", "net", "balance"), values))
            elif line.startswith(b"CAT|"):
                _, cat, income, expense = line.split(b"|")
                data["categories"].append({"id": int(cat), "name": CATEGORIES[int(cat)-1],
                                           "income": int(income), "expenses": int(expense)})
        data["transactions"].sort(key=lambda row: (row["date"], row["id"]), reverse=True)
        return data


def seed_demo(engine):
    if (engine.folder / "lancamentos.dat").exists():
        return
    today = dt.date.today()
    def add(day, kind, cat, amount, description):
        engine.add({"date": today.replace(day=day).isoformat(), "type": kind, "category": cat,
                    "amount": amount, "description": description})
    for row in [(1,"R",1,"5200","Salário do mês"), (2,"D",3,"1450","Aluguel"),
                (3,"D",9,"189.90","Energia elétrica"), (4,"D",4,"328.70","Compras no mercado"),
                (5,"D",5,"160","Transporte"), (6,"D",6,"85.50","Farmácia"),
                (7,"R",2,"650","Projeto extra"), (8,"D",7,"89.90","Curso de programação"),
                (9,"D",4,"74.90","Feira da semana"), (10,"D",8,"120","Cinema e jantar")]:
        add(*row)


def make_handler(engine, token, demo):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, content, mime="application/json; charset=utf-8", filename=None):
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False).encode("utf-8")
            if isinstance(content, str):
                content = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(content)

        def authorized(self, api=False):
            port = self.server.server_port
            hosts = (f"127.0.0.1:{port}", f"localhost:{port}")
            if self.headers.get("Host") not in hosts:
                self.send(403, {"error": "Endereço não autorizado."}); return False
            origin = self.headers.get("Origin")
            if origin and origin not in tuple("http://"+host for host in hosts):
                self.send(403, {"error": "Origem não autorizada."}); return False
            if api and not secrets.compare_digest(self.headers.get("X-App-Token", ""), token):
                self.send(403, {"error": "Reabra a página da aplicação."}); return False
            return True

        def dates(self):
            query = parse_qs(urlsplit(self.path).query)
            today = dt.date.today()
            start = query.get("start", [today.replace(day=1).isoformat()])[0]
            end = query.get("end", [today.replace(day=calendar.monthrange(today.year,today.month)[1]).isoformat()])[0]
            return start, end

        def do_GET(self):
            path = urlsplit(self.path).path
            if not self.authorized(path.startswith("/api/")): return
            try:
                if path in ("/", "/app.js", "/style.css"):
                    file = ROOT / "web" / ({"/":"index.html"}.get(path, path[1:]))
                    data = file.read_text(encoding="utf-8").replace("__APP_TOKEN__", token)
                    mime = {"/":"text/html", "/app.js":"text/javascript", "/style.css":"text/css"}[path]
                    self.send(200, data, mime+"; charset=utf-8")
                elif path == "/api/state":
                    data = engine.state(*self.dates())
                    data["demo"] = demo
                    self.send(200, data)
                elif path == "/api/export":
                    data = engine.state(*self.dates())
                    stream = io.StringIO(newline="")
                    writer = csv.writer(stream, delimiter=";")
                    writer.writerow(["ID", "Data", "Tipo", "Categoria", "Descrição", "Valor (R$)"])
                    for row in data["transactions"]:
                        desc = row["description"]
                        if desc.startswith(("=", "+", "-", "@")): desc = "'" + desc
                        writer.writerow([row["id"], row["date"], "Receita" if row["type"]=="R" else "Despesa",
                                         CATEGORIES[row["category"]-1], desc,
                                         f'{row["cents"]//100},{row["cents"]%100:02}'])
                    self.send(200, b"\xef\xbb\xbf"+stream.getvalue().encode("utf-8"),
                              "text/csv; charset=utf-8", "lancamentos.csv")
                elif path == "/api/backup":
                    with engine.lock:
                        file = engine.folder / "lancamentos.dat"
                        content = file.read_bytes() if file.exists() else b""
                    self.send(200, content, "application/octet-stream", "lancamentos.dat")
                else: self.send(404, {"error":"Página não encontrada."})
            except ValueError as e: self.send(400, {"error":str(e)})
            except (RuntimeError, OSError, UnicodeError):
                self.send(500, {"error":"Não foi possível ler os dados. Confira o terminal e restaure um backup se o histórico estiver inválido."})

        def do_POST(self):
            if not self.authorized(True): return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 4096: raise ValueError("Requisição inválida.")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict): raise ValueError("Dados inválidos.")
                path = urlsplit(self.path).path
                if path == "/api/transactions":
                    self.send(201, {"id":engine.add(data)})
                elif path == "/api/cancel":
                    engine.cancel(data.get("id")); self.send(200, {"ok":True})
                else: self.send(404, {"error":"Operação não encontrada."})
            except (ValueError, UnicodeError) as e: self.send(400, {"error":str(e)})
            except (RuntimeError, OSError) as e: self.send(500, {"error":str(e)})
    return Handler


def main():
    parser = argparse.ArgumentParser(description="Despertar Financeiro: finanças pessoais em COBOL")
    parser.add_argument("--demo", action="store_true", help="Dados fictícios separados dos dados pessoais")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args()
    try:
        binary = build()
        if args.build_only:
            print("Compilado:", binary); return
        folder = args.data_dir or ROOT / ("dados_demo" if args.demo else "dados")
        lock = DataLock(folder)  # mantém referência enquanto o servidor existir
        engine = Engine(binary, folder)
        if args.demo: seed_demo(engine)
        server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(engine, secrets.token_urlsafe(32), args.demo))
        server.daemon_threads = True
        url = f"http://127.0.0.1:{server.server_port}"
        print("Despertar Financeiro | " + ("DEMONSTRAÇÃO" if args.demo else "DADOS PESSOAIS"))
        print("Dados:", folder.resolve())
        print("Abra", url, "| Ctrl+C para encerrar.", flush=True)
        if not args.no_browser: webbrowser.open(url)
        try: server.serve_forever()
        finally:
            server.server_close()
            lock.file.close()
    except KeyboardInterrupt: print("\nAplicação encerrada.")
    except (RuntimeError, OSError, ValueError) as e:
        print("Erro:", e, file=sys.stderr); sys.exit(1)


if __name__ == "__main__":
    main()
