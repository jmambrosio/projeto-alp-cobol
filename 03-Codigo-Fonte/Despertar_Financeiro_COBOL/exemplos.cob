       >>SOURCE FORMAT FREE
identification division.
program-id. exemplos.
data division.
working-storage section.
78 taxa value 0.10.
01 saldo pic 9(5)v99 comp-3 value 100.
01 exibicao pic zz,zz9.99.
01 pessoa.
   05 nome pic x(20) value "Joao".
   05 idade pic 99 value 22.
01 tabela.
   05 nota pic 99 occurs 3 times.
01 i binary-long.
01 estado pic x value "A".
   88 ativo value "A".
01 texto pic x(30) value spaces.
01 ponteiro usage pointer value null.
01 entrada pic x(5) value "12.50".
01 compacto pic s9(7) comp-3 value zero.
procedure division.
principal.
    display "NOME: " function trim(nome)
    compute saldo = saldo + saldo * taxa
    perform mostrar-saldo
    move 7 to nota(1)
    move 8 to nota(2)
    move 9 to nota(3)
    perform varying i from 1 by 1 until i > 3
        display "NOTA: " nota(i)
    end-perform
    if ativo display "ESTADO: ATIVO" end-if
    evaluate idade
        when < 18 display "FAIXA: MENOR"
        when other display "FAIXA: ADULTO"
    end-evaluate
    string "Ola, " function trim(nome)
        delimited by size into texto
        on overflow display "TEXTO SEM ESPACO"
    end-string
    display "TEXTO: " function trim(texto)
    display "NUMVAL: " function numval(entrada)
    display "BYTES COMP-3: " function length(compacto)
    allocate 16 characters returning ponteiro
    if ponteiro not = null
        display "MEMORIA: ALOCADA"
        free ponteiro
    end-if
    stop run.
mostrar-saldo.
    move saldo to exibicao
    display "SALDO: " function trim(exibicao).
