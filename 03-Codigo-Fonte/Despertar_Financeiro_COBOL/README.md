# Despertar Financeiro

Controle financeiro pessoal com motor em **COBOL** e interface gráfica local no navegador.

O nome representa um convite a olhar os hábitos financeiros com mais consciência e fazer mudanças no dia a dia. A interface combina uma base clara, verde-sálvia e detalhes dourados discretos.

Trabalho individual de **João Matheus Ambrosio Sandi**, para Arquitetura de Linguagens de Programação.

## O que está implementado

- Cadastro de receitas e despesas com data, categoria, descrição e valor.
- Consulta por mês ou intervalo de datas; busca por descrição e filtros por tipo e categoria.
- Receitas, despesas e resultado do período; resultado acumulado até a data final.
- Distribuição das despesas por categoria em barras proporcionais.
- Cancelamento de um lançamento incorreto, conservando o registro no histórico.
- Exportação CSV para planilha e download do arquivo de backup.
- Modo de demonstração com dados fictícios, separado dos dados pessoais.

O programa registra valores recebidos ou pagos. Não é um aplicativo bancário: não se conecta a bancos, não realiza pagamentos e não calcula investimentos. O saldo pode ser negativo, pois uma despesa real precisa ser registrada mesmo quando supera as receitas.

## Executar

Requisitos: **Python 3.9 ou superior**, **GnuCOBOL** com o comando `cobc` e sua cadeia de compilação funcionando, e um navegador atualizado. Python usa apenas sua biblioteca padrão; não há `pip install` ou dependências JavaScript para instalar.

Extraia o ZIP antes de executar. Abra um terminal na pasta que contém `app.py`.

### Linux ou WSL

Confira as ferramentas:

```sh
python3 --version
cobc -V
```

Compile, teste e abra a demonstração:

```sh
python3 app.py --build-only
python3 testar.py
python3 app.py --demo
```

### Windows com Python e GnuCOBOL configurados

```powershell
py -3 --version
cobc -V
py -3 app.py --build-only
py -3 testar.py
py -3 app.py --demo
```

Também é possível abrir `iniciar_demo.bat`. O GnuCOBOL deve estar acessível no mesmo terminal usado para iniciar Python, incluindo as bibliotecas necessárias. Se `cobc -V` funcionar mas a compilação falhar, confira a instalação da cadeia de compilação C. O ZIP não inclui compilador nem executável pronto.

O navegador abre em `http://127.0.0.1:8765`. Se não abrir automaticamente, copie o endereço informado no terminal. Mantenha o terminal aberto; use **Ctrl+C** para encerrar. Se a porta estiver ocupada, execute `python3 app.py --demo --port 8766` ou o equivalente com `py -3`.

Para começar com seus próprios dados, encerre a demonstração e execute:

```sh
python3 app.py
```

No Windows, use `py -3 app.py` ou `iniciar.bat`. Essa execução começa vazia, na pasta `dados`. A demonstração usa `dados_demo`. Reabrir preserva os dados de cada modo. Para reiniciar apenas a demonstração, encerre o programa e renomeie a pasta `dados_demo`; a próxima execução com `--demo` cria outra base fictícia.

## Como entender os números

| Indicador | Significado |
| --- | --- |
| Receitas do período | Soma dos recebimentos ativos dentro das datas selecionadas |
| Despesas do período | Soma dos pagamentos ativos dentro das datas selecionadas |
| Resultado do período | Receitas menos despesas nas datas selecionadas |
| Resultado acumulado | Receitas menos despesas de todos os lançamentos ativos desde o início do histórico até a data final |

O resultado acumulado soma os lançamentos ativos desde o início do histórico até a data final. Ele não conhece o dinheiro que já existia quando o controle começou e não consulta o saldo bancário. Por isso, não é necessariamente igual ao total disponível na casa.

O resultado reflete somente os lançamentos cadastrados. Não representa automaticamente o saldo bancário real. Nesta versão não há ajuste separado de saldo inicial. Para acompanhar corretamente, comece a registrar as entradas e saídas a partir de uma data definida e confira o dinheiro disponível separadamente. Não lance um saldo anterior como salário, pois isso distorceria as receitas. Categorias são fixas; não há separação por conta, orçamento planejado, parcelas, contas a vencer ou conciliação bancária.

Ao corrigir um lançamento, cancele o incorreto e cadastre o correto. O cancelamento retira o original de todos os relatórios, inclusive os de períodos anteriores. Ele corrige o cadastro; não representa um estorno financeiro ocorrido na data do cancelamento. O evento original e seu cancelamento permanecem no arquivo.

Filtros de busca, tipo e categoria afetam apenas a lista. Os cartões, as barras e o CSV continuam representando o período completo, conforme indicado na tela.

## Roteiro de demonstração

1. Execute com `--demo` e selecione o mês atual. A carga inicial contém dez lançamentos fictícios.
2. Confira receitas de **R$ 5.850,00**, despesas de **R$ 2.498,90** e resultado de **R$ 3.351,10**.
3. Cadastre uma despesa de **R$ 12,50**, categoria Alimentação, descrição `Lanche de teste`, com uma data do mês exibido. O resultado passa a **R$ 3.338,60**.
4. Busque `Lanche`, filtre a categoria e observe que os cartões continuam mostrando o período inteiro.
5. Cancele esse lançamento. O resultado volta a **R$ 3.351,10**.
6. Tente um valor como `1,234`. A entrada deve ser recusada porque tem mais de duas casas decimais.
7. Exporte o CSV e baixe o backup. Encerre e reabra a demonstração para verificar a persistência.

Datas da base fictícia vão do dia 1 ao dia 10 do mês corrente, independentemente do dia da apresentação. Todos esses valores são exemplos.

## Organização do código

| Arquivo | Responsabilidade |
| --- | --- |
| `financas.cob` | Validar o protocolo e o histórico, cadastrar, cancelar, calcular totais e gravar registros |
| `app.py` | Compilar/invocar o COBOL, converter formatos, atender HTTP local e exportar arquivos |
| `web/index.html` | Estrutura das telas e formulários |
| `web/style.css` | Aparência e adaptação a diferentes larguras de tela |
| `web/app.js` | Interações, requisições e apresentação dos resultados |
| `testar.py` | Dezesseis testes automatizados com dados temporários |
| `exemplos.cob` | Exemplos adicionais relacionados ao tutorial do relatório |
| `docs/ESTUDO.md` | Explicação do fluxo e perguntas para a apresentação |

O navegador envia JSON para Python. Python converte a requisição para um protocolo textual e executa o programa COBOL. O COBOL lê o histórico, valida a operação, calcula ou grava, e devolve o resultado. Python converte essa resposta para JSON. JavaScript apresenta os valores e calcula somente proporções visuais; os totais financeiros vêm do COBOL.

## Representação e persistência

Os valores são transmitidos como inteiros em centavos. No COBOL, o valor de uma operação usa `PIC 9(7)V99 COMP-3`; os acumuladores têm doze dígitos inteiros e duas casas decimais. Não se utiliza ponto flutuante para os cálculos financeiros.

`lancamentos.dat` é um arquivo `LINE SEQUENTIAL`, com 99 bytes por registro, sem contar o terminador de linha:

| Campo | Bytes | Conteúdo |
| --- | ---: | --- |
| ID | 9 | Sequência de eventos |
| Alvo | 9 | ID cancelado, ou zero para receita/despesa |
| Data | 8 | AAAAMMDD |
| Tipo | 1 | R, D ou C |
| Categoria | 2 | 01 a 12; 00 no cancelamento |
| Valor | 9 | Centavos, sem separador decimal |
| Descrição | 60 | Texto UTF-8 completado com espaços |
| Final | 1 | Marcador # |

A descrição admite até 60 **bytes**, não necessariamente 60 letras: acentos em UTF-8 podem ocupar mais de um byte. O marcador final preserva os espaços internos do layout. O leitor aceita um buffer maior para detectar registros de tamanho inesperado.

Cada comando recarrega o arquivo e recompõe uma tabela `OCCURS 10000`. Isso permite identificar lançamentos cancelados. O limite é de **10.000 eventos**, contando cadastros e cancelamentos. Cada valor deve estar entre R$ 0,01 e R$ 9.999.999,99. Não edite o arquivo manualmente.

Os códigos de saída do motor são 0 para sucesso, 2 para entrada inválida, 3 para histórico inválido e 4 para falha de arquivo. A gravação é confirmada somente após `WRITE` e `CLOSE` sem erro detectado.

## Backup e limites

O botão **Baixar backup** copia o histórico completo. Guarde cópias com data em outro local. O CSV exporta apenas lançamentos ativos do período e **não substitui um backup**.

Para restaurar: encerre a aplicação, preserve uma cópia do arquivo atual, copie o backup para `dados/lancamentos.dat` (ou `dados_demo/lancamentos.dat`, se for a demonstração) e reabra. Não misture os modos. O formato novo não importa automaticamente o antigo `movimentos.dat`.

A aplicação escuta somente em `127.0.0.1`, verifica Host/Origin e usa um token por execução para suas requisições. Há bloqueio de uma segunda instância sobre a mesma pasta e serialização das operações na ponte Python. Execute o motor por essa ponte; chamadas independentes ao executável COBOL não compartilham esse bloqueio.

Essas medidas não constituem autenticação de usuários nem criptografia. Os arquivos ficam legíveis no computador. O projeto não oferece transações atômicas, recuperação automática de escrita interrompida ou garantia contra perda de dados. Histórico inválido bloqueia as operações; restaure uma cópia válida. Não exponha este servidor à internet.

## Verificação realizada

O motor foi compilado com **GnuCOBOL 3.1.2, `-Wall -debug`, em Linux**, e os **16 testes de `testar.py` passaram** durante a preparação assistida. A suíte cobre centavos exatos, persistência, períodos, saldo negativo, cancelamento, entradas inválidas, calendário, limites, UTF-8, histórico corrompido, falhas de arquivo, serialização, capacidade, protocolo, demonstração, bloqueio de instância e HTTP/exportação/backup.

A conferência visual e os testes completos de interação em navegador ficaram bloqueados por uma restrição do ambiente de preparação. A execução em Windows e na máquina da apresentação ainda precisa ser conferida. Use o roteiro acima antes da entrega. A suíte não testa perda de energia nem demonstra adequação a uso bancário.

## Preparar o GitHub

Envie os fontes, a pasta `web`, a pasta `docs` e o README. O `.gitignore` exclui executáveis, dados e backups; não publique sua base financeira. Se enviar arquivos pelo navegador do GitHub, respeite essas exclusões manualmente.

O GitHub armazena o código. **GitHub Pages não executa Python nem COBOL**: a aplicação é executada localmente. Coloque o relatório e os slides finais no repositório se isso fizer parte da organização da entrega; depois use o link solicitado na atividade. Este pacote ainda não foi publicado nem entregue.

## Referências técnicas

- [GnuCOBOL Programmer’s Guide](https://gnucobol.sourceforge.io/HTML/gnucobpg.html)
- [GnuCOBOL Manual](https://gnucobol.sourceforge.io/doc/gnucobol.html)
- [Python: http.server](https://docs.python.org/3/library/http.server.html)

Houve assistência de inteligência artificial na preparação do código, da documentação e dos testes. A compreensão, a revisão final e a apresentação são responsabilidade do aluno.
