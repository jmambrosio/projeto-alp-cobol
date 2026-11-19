       >>source format free
identification division.
program-id. financas.
*> Motor financeiro. Interface e transporte ficam em app.py/web.
environment division.
input-output section.
file-control.
    select optional diario assign to "lancamentos.dat"
        organization is line sequential file status is fs.
data division.
file section.
fd diario record is varying from 1 to 512
    depending on tamanho-registro.
01 linha.
   05 reg-id pic 9(9).
   05 reg-alvo pic 9(9).
   05 reg-data pic 9(8).
   05 reg-tipo pic x.
   05 reg-categoria pic 99.
   05 reg-valor pic 9(7)v99.
   05 reg-descricao pic x(60).
   05 reg-fim pic x.
   05 filler pic x(413).
working-storage section.
78 capacidade value 10000.
01 fs pic xx.
01 tamanho-registro binary-long.
01 comando pic x(512).
01 entrada pic x(512).
01 data-inicio pic 9(8).
01 data-final pic 9(8).
01 novo-tipo pic x.
01 nova-data pic 9(8).
01 nova-categoria pic 99.
01 novo-valor pic 9(7)v99 comp-3.
01 nova-descricao pic x(60).
01 alvo binary-long.
01 ultimo binary-long value 0.
01 i binary-long.
01 categoria binary-long.
01 fim pic 9 value 0.
   88 terminou value 1.
01 mensagem pic x(120).
01 erro-saida binary-long value 2.
01 registros.
   05 item occurs 10000 times.
      10 ativo pic 9.
      10 conteudo.
         15 item-id pic 9(9).
         15 item-alvo pic 9(9).
         15 item-data pic 9(8).
         15 item-tipo pic x.
         15 item-categoria pic 99.
         15 item-valor pic 9(7)v99.
         15 item-descricao pic x(60).
         15 item-fim pic x.
01 totais-categorias.
   05 total-categoria occurs 12 times.
      10 receitas-cat pic 9(12)v99 comp-3.
      10 despesas-cat pic 9(12)v99 comp-3.
01 receitas pic 9(12)v99 comp-3 value zero.
01 despesas pic 9(12)v99 comp-3 value zero.
01 acumulado pic s9(12)v99 comp-3 value zero.
01 resultado pic s9(12)v99 comp-3 value zero.
01 cents-r pic 9(14).
01 cents-d pic 9(14).
01 cents-s pic +9(14).
01 cents-a pic +9(14).
01 cat-saida pic 99.

procedure division.
principal.
    initialize registros totais-categorias
    accept comando
    move function trim(comando) to comando
    if comando not = "LIST" and not = "ADD" and not = "CANCEL"
        move "Comando desconhecido." to mensagem
        perform falhar
    end-if
    perform carregar-diario
    evaluate comando
        when "LIST" perform listar
        when "ADD" perform cadastrar
        when "CANCEL" perform cancelar
    end-evaluate
    stop run.

carregar-diario.
    open input diario
    if fs = "05" move 1 to fim
    else
        if fs not = "00" perform erro-arquivo end-if
    end-if
    perform until terminou
        read diario
        evaluate fs
            when "10" move 1 to fim
            when "00" perform aplicar-registro
            when "04" perform erro-historico
            when other perform erro-arquivo
        end-evaluate
    end-perform
    close diario
    if fs not = "00" perform erro-arquivo end-if.

aplicar-registro.
    if tamanho-registro not = 99 or reg-fim not = "#"
        or reg-id is not numeric or reg-alvo is not numeric
        or reg-data is not numeric or reg-categoria is not numeric
        or reg-valor is not numeric
        perform erro-historico
    end-if
    if ultimo >= capacidade or reg-id not = ultimo + 1
        perform erro-historico
    end-if
    if function test-date-yyyymmdd(reg-data) not = 0
        perform erro-historico
    end-if
    evaluate reg-tipo
        when "R" when "D"
            if reg-alvo not = 0 or reg-valor = 0
                or reg-categoria < 1 or reg-categoria > 12
                or reg-descricao = spaces
                perform erro-historico
            end-if
            add 1 to ultimo
            move linha(1:99) to conteudo(ultimo)
            move 1 to ativo(ultimo)
        when "C"
            if reg-alvo < 1 or reg-alvo > ultimo
                or reg-categoria not = 0 or reg-valor not = 0
                perform erro-historico
            end-if
            move reg-alvo to alvo
            if ativo(alvo) not = 1 perform erro-historico end-if
            move 0 to ativo(alvo)
            add 1 to ultimo
        when other perform erro-historico
    end-evaluate.

ler-data.
    accept entrada
    if function length(function trim(entrada)) not = 8
        or entrada(1:8) is not numeric
        move "Data invalida. Use AAAAMMDD." to mensagem
        perform falhar
    end-if
    move entrada(1:8) to nova-data
    if function test-date-yyyymmdd(nova-data) not = 0
        move "Data inexistente no calendario." to mensagem
        perform falhar
    end-if.

cadastrar.
    accept entrada
    if function trim(entrada) not = "R" and not = "D"
        move "Tipo invalido: use R ou D." to mensagem
        perform falhar
    end-if
    move function trim(entrada) to novo-tipo
    perform ler-data
    accept entrada
    if function length(function trim(entrada)) not = 2
        or entrada(1:2) is not numeric
        move "Categoria invalida." to mensagem perform falhar
    end-if
    move entrada(1:2) to nova-categoria
    if nova-categoria < 1 or nova-categoria > 12
        move "Categoria deve estar entre 01 e 12." to mensagem
        perform falhar
    end-if
    *> Transporte em centavos, nove digitos. Nenhum ponto flutuante.
    accept entrada
    if function length(function trim(entrada)) not = 9
        or entrada(1:9) is not numeric
        move "Valor invalido: informe nove digitos em centavos."
            to mensagem
        perform falhar
    end-if
    compute novo-valor = function numval(entrada(1:9)) / 100
    if novo-valor = 0
        move "O valor deve ser positivo." to mensagem perform falhar
    end-if
    accept entrada
    if function trim(entrada) = spaces
        or function length(function trim(entrada)) > 60
        move "Descricao deve ter entre 1 e 60 bytes UTF-8."
            to mensagem
        perform falhar
    end-if
    move function trim(entrada) to nova-descricao
    initialize linha
    move novo-tipo to reg-tipo
    move nova-data to reg-data
    move nova-categoria to reg-categoria
    move novo-valor to reg-valor
    move nova-descricao to reg-descricao
    perform gravar
    display "OK|" reg-id.

cancelar.
    accept entrada
    if function length(function trim(entrada)) not = 9
        or entrada(1:9) is not numeric
        move "Identificador invalido." to mensagem perform falhar
    end-if
    compute alvo = function numval(entrada(1:9))
    if alvo < 1 or alvo > ultimo
        move "Lancamento nao encontrado." to mensagem perform falhar
    end-if
    if ativo(alvo) not = 1
        move "Lancamento ja cancelado." to mensagem perform falhar
    end-if
    perform ler-data
    initialize linha
    move "C" to reg-tipo
    move alvo to reg-alvo
    move nova-data to reg-data
    move "CANCELAMENTO" to reg-descricao
    perform gravar
    display "OK|" reg-id.

gravar.
    if ultimo >= capacidade
        move "Limite de 10000 eventos atingido." to mensagem
        perform falhar
    end-if
    compute reg-id = ultimo + 1
    move "#" to reg-fim
    move 99 to tamanho-registro
    open extend diario
    if fs not = "00" and not = "05" perform erro-arquivo end-if
    write linha
    if fs not = "00" perform erro-arquivo end-if
    close diario
    if fs not = "00" perform erro-arquivo end-if.

listar.
    perform ler-data
    move nova-data to data-inicio
    perform ler-data
    move nova-data to data-final
    if data-final < data-inicio
        move "Data final anterior a inicial." to mensagem
        perform falhar
    end-if
    perform varying i from 1 by 1 until i > ultimo
        if ativo(i) = 1
            if item-data(i) <= data-final
                if item-tipo(i) = "R"
                    add item-valor(i) to acumulado
                else subtract item-valor(i) from acumulado end-if
            end-if
            if item-data(i) >= data-inicio
                and item-data(i) <= data-final
                move item-categoria(i) to categoria
                if item-tipo(i) = "R"
                    add item-valor(i) to receitas
                        receitas-cat(categoria)
                else
                    add item-valor(i) to despesas
                        despesas-cat(categoria)
                end-if
                display "ROW|" conteudo(i)
            end-if
        end-if
    end-perform
    compute resultado = receitas - despesas
    compute cents-r = receitas * 100
    compute cents-d = despesas * 100
    compute cents-s = resultado * 100
    compute cents-a = acumulado * 100
    display "TOTAL|" cents-r "|" cents-d "|" cents-s "|" cents-a
    perform varying categoria from 1 by 1 until categoria > 12
        move categoria to cat-saida
        compute cents-r = receitas-cat(categoria) * 100
        compute cents-d = despesas-cat(categoria) * 100
        display "CAT|" cat-saida "|" cents-r "|" cents-d
    end-perform.

erro-historico.
    move 3 to erro-saida
    move "Historico invalido. Restaure uma copia de seguranca."
        to mensagem
    perform falhar.
erro-arquivo.
    move 4 to erro-saida
    move spaces to mensagem
    string "Erro de arquivo. FILE STATUS: " fs
        into mensagem end-string
    perform falhar.
falhar.
    display "ERROR|" function trim(mensagem)
    stop run returning erro-saida.
