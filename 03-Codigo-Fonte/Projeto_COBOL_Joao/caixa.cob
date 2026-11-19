       >>SOURCE FORMAT FREE
identification division.
program-id. caixa-didatico.
*> Implementacao didatica preparada com assistencia de IA.
*> Uma conta, um processo por vez. Valores com ponto decimal.
environment division.
input-output section.
file-control.
    select optional movimentos assign to "movimentos.dat"
        organization is line sequential
        file status is status-arquivo.
data division.
file section.
fd movimentos
    record is varying in size from 1 to 100
        depending on tamanho-registro.
01 registro.
   05 operacao-gravada pic x.
   05 valor-gravado pic 9(7)v99.
   05 filler pic x(90).
working-storage section.
78 limite-saldo value 9999999.99.
01 status-arquivo pic xx.
01 tamanho-registro binary-long.
01 saldo pic 9(7)v99 comp-3 value zero.
01 novo-saldo pic 9(7)v99 comp-3 value zero.
01 valor pic 9(7)v99 comp-3 value zero.
01 valor-tela pic z,zzz,zz9.99.
01 opcao pic x(80).
01 entrada pic x(80).
01 operacao pic x.
01 descricao pic x(8).
01 fim-arquivo pic 9 value zero.
   88 terminou-arquivo value 1.
01 fim-programa pic 9 value zero.
   88 sair value 1.
01 validade pic 9 value zero.
   88 valor-valido value 1.
01 tamanho binary-long value zero.
01 posicao binary-long value zero.
01 pontos binary-long value zero.
01 inteiros binary-long value zero.
01 decimais binary-long value zero.
01 caractere pic x.
01 numero-linha binary-long value zero.
01 contador-tela pic zzzzz9.

procedure division.
principal.
    perform carregar-saldo
    display "CAIXA DIDATICO - COBOL"
    display "Conta unica. Use ponto decimal: 10.50"
    perform until sair
        display " "
        display "1 Saldo | 2 Deposito | 3 Saque | 4 Extrato | 0 Sair"
        accept opcao on exception move "0" to opcao end-accept
        evaluate function trim(opcao)
            when "1" perform mostrar-saldo
            when "2"
                move "D" to operacao
                perform movimentar
            when "3"
                move "S" to operacao
                perform movimentar
            when "4" perform mostrar-extrato
            when "0" set sair to true
            when other display "Opcao invalida."
        end-evaluate
    end-perform
    display "Encerrado. Movimentacoes preservadas no arquivo."
    stop run.

mostrar-saldo.
    move saldo to valor-tela
    display "Saldo: R$ " function trim(valor-tela).

abrir-leitura.
    move zero to fim-arquivo numero-linha
    open input movimentos
    evaluate status-arquivo
        when "00" continue
        when "05" set terminou-arquivo to true
        when other perform erro-arquivo
    end-evaluate.

ler-registro.
    read movimentos
    evaluate status-arquivo
        when "10" set terminou-arquivo to true
        when "00"
            add 1 to numero-linha
            if tamanho-registro not = 10
                or (operacao-gravada not = "D"
                    and operacao-gravada not = "S")
                or valor-gravado is not numeric
                perform erro-registro
            end-if
            if valor-gravado = zero perform erro-registro end-if
        when other perform erro-arquivo
    end-evaluate.

fechar-arquivo.
    close movimentos
    if status-arquivo not = "00" perform erro-arquivo end-if.

carregar-saldo.
    move zero to saldo
    perform abrir-leitura
    perform until terminou-arquivo
        perform ler-registro
        if not terminou-arquivo
            evaluate operacao-gravada
                when "D"
                    add valor-gravado to saldo
                        on size error perform erro-registro
                    end-add
                when "S"
                    if valor-gravado > saldo
                        perform erro-registro
                    end-if
                    subtract valor-gravado from saldo
            end-evaluate
        end-if
    end-perform
    perform fechar-arquivo.

movimentar.
    perform ler-valor
    if not valor-valido
        display "Valor invalido. Use 0.01 a 9999999.99, sem separador de milhar."
        exit paragraph
    end-if
    move saldo to novo-saldo
    if operacao = "D"
        if valor > limite-saldo - saldo
            display "Deposito rejeitado: limite do saldo."
            exit paragraph
        end-if
        add valor to novo-saldo
            on size error
                display "Deposito rejeitado: limite numerico."
                exit paragraph
        end-add
    else
        if valor > saldo
            display "Saque rejeitado: saldo insuficiente."
            exit paragraph
        end-if
        subtract valor from novo-saldo
    end-if
    *> Grava primeiro. Atualiza a memoria depois de confirmar a escrita.
    perform gravar-movimento
    move novo-saldo to saldo
    display "Operacao registrada."
    perform mostrar-saldo.

ler-valor.
    move zero to validade pontos inteiros decimais valor
    display "Valor: "
    accept entrada on exception move spaces to entrada end-accept
    move function trim(entrada) to entrada
    compute tamanho = function length(function trim(entrada))
    if tamanho = zero or tamanho > 10 exit paragraph end-if
    perform varying posicao from 1 by 1 until posicao > tamanho
        move entrada(posicao:1) to caractere
        evaluate true
            when caractere = "."
                add 1 to pontos
                if pontos > 1 exit paragraph end-if
            when caractere >= "0" and caractere <= "9"
                if pontos = zero
                    add 1 to inteiros
                else
                    add 1 to decimais
                end-if
            when other exit paragraph
        end-evaluate
    end-perform
    if inteiros < 1 or inteiros > 7 or decimais > 2
        or (pontos = 1 and decimais = zero)
        exit paragraph
    end-if
    compute valor = function numval(entrada)
    if valor > zero set valor-valido to true end-if.

gravar-movimento.
    open extend movimentos
    if status-arquivo not = "00" and status-arquivo not = "05"
        perform erro-arquivo
    end-if
    initialize registro
    move operacao to operacao-gravada
    move valor to valor-gravado
    move 10 to tamanho-registro
    write registro
    if status-arquivo not = "00" perform erro-arquivo end-if
    perform fechar-arquivo.

mostrar-extrato.
    display "EXTRATO"
    perform abrir-leitura
    perform until terminou-arquivo
        perform ler-registro
        if not terminou-arquivo
            if operacao-gravada = "D"
                move "DEPOSITO" to descricao
            else
                move "SAQUE" to descricao
            end-if
            move numero-linha to contador-tela
            move valor-gravado to valor-tela
            display function trim(contador-tela) " " descricao
                " R$ " function trim(valor-tela)
        end-if
    end-perform
    if numero-linha = zero display "Sem movimentacoes." end-if
    perform fechar-arquivo
    perform mostrar-saldo.

erro-arquivo.
    display "Erro de arquivo. FILE STATUS: " status-arquivo
    display "Programa interrompido. Confira a pasta e as permissoes."
    stop run returning 1.

erro-registro.
    move numero-linha to contador-tela
    display "Historico invalido na linha " function trim(contador-tela)
    display "Programa interrompido sem incluir novas movimentacoes."
    stop run returning 2.
