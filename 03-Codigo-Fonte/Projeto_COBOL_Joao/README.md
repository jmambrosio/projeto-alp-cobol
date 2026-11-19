# Caixa didático em COBOL

Material para o trabalho individual de João Matheus Ambrosio Sandi, em Arquitetura de Linguagens de Programação. Implementação preparada com assistência de IA e verificação automatizada.

## Arquivos

- `caixa.cob`: programa com saldo, depósito, saque e extrato.
- `exemplos.cob`: demonstrações de registros, tabelas, nível 88, STRING, função, constante e memória dinâmica.
- `testar.py`: testes de comportamento que criam diretórios temporários separados.
- `Makefile`: comandos opcionais de compilação e teste.

## Compilar e executar

É necessário ter GnuCOBOL e sua cadeia de compilação instalados. A versão usada na verificação foi GnuCOBOL 3.1.2 em Linux. Consulte os downloads oficiais em https://gnucobol.sourceforge.io/ . No Windows, use uma instalação de GnuCOBOL que tenha o compilador C configurado, ou um ambiente Linux no WSL já preparado. Não é necessário mainframe.

Na pasta dos fontes:

```sh
cobc -x -free -Wall -debug -o caixa caixa.cob
cobc -x -free -Wall -debug -o exemplos exemplos.cob
```

Linux:

```sh
./exemplos
./caixa
```

Para compilar nativamente no Windows, com GnuCOBOL instalado e disponível no terminal:

```powershell
cobc -x -free -Wall -debug -o caixa.exe caixa.cob
cobc -x -free -Wall -debug -o exemplos.exe exemplos.cob
```

No PowerShell, os executáveis Windows são iniciados com `./exemplos.exe` e `./caixa.exe`. Um binário Linux não é um executável Windows. Faça um teste completo na máquina da apresentação.

## Operação

O saldo inicial é zero. O menu aceita 1 para saldo, 2 para depósito, 3 para saque, 4 para extrato e 0 para sair. Digite valores como `50.25`, com ponto decimal e sem separador de milhar. São aceitos até sete dígitos inteiros e duas casas decimais. Saques e depósitos precisam ser positivos.

O programa cria `movimentos.dat` no diretório atual. Cada linha contém D ou S seguido de nove dígitos, com as duas últimas posições representando os centavos. O programa lê todo o histórico ao iniciar e calcula o saldo. Não existe um arquivo de saldo separado. Não edite o histórico durante a execução e não abra duas instâncias ao mesmo tempo.

## Demonstração

1. Execute em uma pasta nova, sem histórico. Consulte o saldo: 0.00.
2. Deposite 50.25 e saque 20.10.
3. Consulte o extrato. O saldo deve ser 30.15.
4. Saia e abra novamente na mesma pasta. O saldo permanece 30.15.
5. Tente sacar 100.00. O saque será recusado.
6. Tente depositar `1,50`. A entrada será recusada. O formato adotado usa ponto.

Para repetir com saldo zero, use outra pasta vazia. Preserve qualquer histórico que deseje manter.

## Testes

Python 3 é necessário apenas para executar os testes, não para usar o caixa.

```sh
python3 testar.py ./caixa
```

No Windows, após compilar nativamente, o equivalente é `py testar.py ./caixa.exe`. Esse ambiente ainda não foi validado neste pacote.

Foram aprovados nove grupos: início vazio; saldo e persistência; saque sem saldo; quinze entradas inválidas; limite numérico; centavos e saldo zero; seis históricos inválidos; erro de gravação; menu inválido. Os testes não alteram o histórico da sua pasta de trabalho.

## Limitações

Protótipo acadêmico de conta única e uso por um processo de cada vez. Não inclui autenticação, segurança bancária, acesso concorrente nem recuperação transacional em caso de interrupção durante uma escrita. Verificar FILE STATUS reduz erros de operação, mas não garante durabilidade contra todas as falhas de hardware. Uma interrupção pode deixar o último registro incompleto; ao detectar histórico inválido, o programa encerra sem acrescentar novas operações.

## Referências

- https://gnucobol.sourceforge.io/doc/gnucobol.html
- https://gnucobol.sourceforge.io/HTML/gnucobpg.html

## Roteiro de leitura do código

Comece em PRINCIPAL. Veja como o menu escolhe a operação. Depois leia MOVIMENTAR e observe a separação entre SALDO e NOVO-SALDO. Estude LER-VALOR para entender a validação. Compare GRAVAR-MOVIMENTO com CARREGAR-SALDO para explicar persistência. Por último, veja MOSTRAR-EXTRATO e os dois parágrafos de erro.

## Registros da verificação

A pasta `verificacao` contém a saída real dos nove grupos de testes, a execução de `exemplos.cob` e a transcrição da demonstração do caixa com as entradas utilizadas. Verificação realizada em 19/11/2026, com GnuCOBOL 3.1.2 em Linux. Esses registros não substituem o teste na máquina da apresentação.

O pacote contém os fontes; os executáveis devem ser compilados no ambiente em que serão usados. O arquivo `movimentos.dat` é criado durante o uso e não está incluído, para que a primeira execução comece com saldo zero.
