"""Testes de comportamento. Uso: python3 testar.py ./caixa"""
import pathlib
import subprocess
import sys
import tempfile

exe = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else './caixa').resolve()
total = 0

def executar(pasta, entrada, esperado=0):
    p = subprocess.run([str(exe)], input=entrada, text=True,
                       cwd=pasta, capture_output=True, timeout=5)
    assert p.returncode == esperado, (p.returncode, p.stdout, p.stderr)
    return p.stdout

def verificar(nome, funcao):
    global total
    with tempfile.TemporaryDirectory() as pasta:
        funcao(pathlib.Path(pasta))
    total += 1
    print('OK', nome)

def inicio(p):
    s = executar(p, '1\n4\n0\n')
    assert 'Saldo: R$ 0.00' in s and 'Sem movimentacoes.' in s

def persistencia(p):
    s = executar(p, '2\n50.25\n3\n20.10\n4\n0\n')
    assert 'Saldo: R$ 30.15' in s and 'DEPOSITO' in s and 'SAQUE' in s
    assert (p/'movimentos.dat').read_text().splitlines() == ['D000005025','S000002010']
    assert 'Saldo: R$ 30.15' in executar(p, '1\n0\n')

def insuficiente(p):
    s = executar(p, '2\n10\n3\n10.01\n1\n0\n')
    assert 'saldo insuficiente' in s and 'Saldo: R$ 10.00' in s
    assert len((p/'movimentos.dat').read_text().splitlines()) == 1

def invalidos(p):
    for v in ['', '0', '-1', '+1', 'abc', '1,50', '1.234', '.', '.50',
              '10.', '1 0', '1e2', '10000000', '1.2.3', '99999999.99']:
        assert 'Valor invalido' in executar(p, '2\n'+v+'\n0\n'), v
    assert not (p/'movimentos.dat').exists()

def limite(p):
    s = executar(p, '2\n9999999.99\n2\n0.01\n0\n')
    assert 'limite do saldo' in s
    assert len((p/'movimentos.dat').read_text().splitlines()) == 1
    assert 'Saldo: R$ 9,999,999.99' in executar(p, '1\n0\n')

def zerar(p):
    s = executar(p, '2\n0.01\n3\n0.01\n0\n')
    assert 'Saldo: R$ 0.00' in s
    assert 'Saldo: R$ 0.00' in executar(p, '1\n0\n')

def corrompidos(p):
    for registro in ['Dabc', 'X000000100', 'D000000000', 'S000000001',
                     'D00000010X', 'D999999999\nD000000001']:
        arq = p/'movimentos.dat'
        arq.write_text(registro+'\n')
        antes = arq.read_bytes()
        s = executar(p, '0\n', esperado=2)
        assert 'Historico invalido' in s
        assert arq.read_bytes() == antes

def acesso(p):
    (p/'movimentos.dat').mkdir()
    assert 'Erro de arquivo' in executar(p, '2\n10\n0\n', esperado=1)

def opcoes(p):
    s = executar(p, 'abc\n7\n12\n1\n0\n')
    assert s.count('Opcao invalida.') == 3
    assert 'Saldo: R$ 0.00' in s

for nome, funcao in [('inicio vazio', inicio), ('saldo e persistencia', persistencia),
                     ('saque sem saldo', insuficiente), ('15 entradas invalidas', invalidos),
                     ('limite numerico', limite), ('centavos e saldo zero', zerar),
                     ('6 historicos invalidos', corrompidos), ('erro de arquivo', acesso),
                     ('menu invalido', opcoes)]:
    verificar(nome, funcao)
print(f'{total} grupos de testes aprovados.')
