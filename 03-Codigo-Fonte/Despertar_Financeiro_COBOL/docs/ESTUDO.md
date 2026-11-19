# Entender e apresentar o Despertar Financeiro

## A ideia em trinta segundos

“O Despertar Financeiro registra receitas e despesas pessoais. A interface funciona no navegador, mas as regras e os cálculos estão em COBOL. Python conecta as duas partes. O projeto demonstra representação decimal, validação, tabelas internas, decisões, repetição e persistência em arquivo.”

## Acompanhe uma despesa de R$ 12,50

1. O formulário recebe tipo, data, categoria, descrição e o texto `12,50`.
2. `Engine.add`, em `app.py`, confere os dados e converte o texto para **1250 centavos**, sem usar `float`.
3. `Engine.run` executa o COBOL, enviando o comando `ADD` e os campos, um por linha.
4. `principal`, em `financas.cob`, carrega e valida o histórico. `EVALUATE` seleciona `cadastrar`.
5. `cadastrar` valida novamente os campos do protocolo. `FUNCTION NUMVAL` converte os nove dígitos de centavos; dividir por 100 gera o valor decimal do campo `COMP-3`.
6. `gravar` atribui o próximo ID, usa `OPEN EXTEND`, escreve o registro e verifica `FILE STATUS`, inclusive após `CLOSE`.
7. O navegador pede uma nova consulta. `listar` soma receitas e despesas e devolve os totais. A interface mostra o resultado atualizado.

Você deve conseguir localizar esses parágrafos no código e explicar o papel de cada um. Não é necessário decorar todas as linhas.

## Onde cada conceito aparece

| Conceito | Trecho concreto |
| --- | --- |
| Divisões | Identificação do programa, arquivo no ambiente, registros nos dados e rotinas no procedimento |
| `PIC` | Define tamanho e escala dos campos |
| `COMP-3` | Representação decimal compactada dos valores de trabalho e acumuladores |
| `OCCURS` | Tabela com até 10.000 eventos e tabela de doze categorias |
| `EVALUATE` | Escolhe LIST, ADD ou CANCEL |
| `PERFORM` | Chama rotinas e percorre os registros |
| Nível 88 | `terminou` nomeia a condição de fim da leitura |
| Funções | `TRIM`, `NUMVAL` e `TEST-DATE-YYYYMMDD` |
| Arquivos | `SELECT`, `FD`, `READ`, `WRITE`, `OPEN`, `CLOSE` e `FILE STATUS` |
| Integração | Entrada/saída textual entre o executável COBOL e o processo Python |

## Perguntas que podem aparecer

**O que realmente está em COBOL?**
A validação do protocolo e do arquivo, os cadastros e cancelamentos, a reconstrução do estado, a soma por período e categoria e a persistência. Python cuida do transporte e dos formatos da interface. JavaScript exibe os resultados.

**Por que usar centavos e COMP-3?**
Centavos inteiros evitam conversões por ponto flutuante na comunicação. A representação decimal preserva exatamente a escala prevista para os valores aceitos. Isso não elimina a necessidade de verificar limites e erros.

**O resultado do mês é igual ao saldo?**
Não necessariamente. O resultado do período usa apenas o intervalo selecionado. O resultado acumulado soma os registros ativos desde o início do histórico até a data final e não inclui o dinheiro existente antes do começo do controle.

**Por que permitir saldo negativo?**
O programa registra a realidade financeira informada. Se uma despesa aconteceu, ela precisa aparecer mesmo quando supera as receitas. Não se trata de autorizar um saque bancário.

**Por que não apagar uma linha ao cancelar?**
O sistema acrescenta um evento C que referencia o ID original. Na leitura seguinte, aquele lançamento fica inativo. O histórico preserva o que foi cadastrado. Esse mecanismo corrige registros; não é um estorno contábil por data.

**Como os dados sobrevivem ao fechamento?**
WORKING-STORAGE existe durante a execução. O arquivo conserva os registros; a execução seguinte o lê e recompõe a tabela e os totais.

**O que acontece com um arquivo inválido?**
A carga confere comprimento, marcador, IDs sequenciais, tipos, datas, categorias e valores. Uma inconsistência detectada interrompe a operação. Não há reparo automático: é preciso preservar o arquivo e restaurar um backup válido.

**Qual é a complexidade?**
A cada comando, o histórico é relido. Carregar e consultar percorrem os eventos: tempo linear na quantidade de registros. O limite de 10.000 eventos mantém a tabela com tamanho definido. Não foi realizado um estudo comparativo de desempenho.

**Por que há Python se o trabalho é de COBOL?**
Para oferecer uma interface gráfica simples sem deslocar as regras financeiras do COBOL. O processo Python chama o executável e traduz as mensagens; os totais são produzidos no núcleo COBOL. A arquitetura exemplifica integração de uma linguagem procedural com uma interface atual.

**Está pronto para qualquer uso?**
É uma aplicação acadêmica local. Não possui múltiplas contas, orçamento planejado, importação bancária, criptografia ou recuperação transacional. Há testes automatizados, mas ainda é necessário executar e conferir a interface na máquina da apresentação.

## Estudo e ensaio

Primeiro, execute a demonstração do README. Depois, acompanhe `principal → carregar-diario → cadastrar → gravar`. Em seguida, leia `listar` para entender os dois resultados financeiros e `cancelar` para entender os eventos. Por último, responda às perguntas acima sem ler e repita a demonstração explicando o que acontece em cada camada.

Use apenas os dados fictícios na apresentação. O modo pessoal pode ser usado depois para praticar o registro e a conferência dos gastos, respeitando os limites descritos no README.
