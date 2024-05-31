from datetime import datetime, timedelta


def verificar_saldo(saldo_remetente, valor_transacao, taxa):
    return saldo_remetente >= (valor_transacao + taxa)


def verificar_horario_transacao(horario_transacao, horario_atual, horario_ultima_transacao):
    return horario_ultima_transacao < horario_transacao <= horario_atual


def verificar_limite_transacoes(transacoes_recentes):
    return transacoes_recentes <= 100


def verificar_chave_validador(chave_recebida, chave_esperada):
    return chave_recebida == chave_esperada


def calcular_tempo_recusa(transacoes_recusadas, base_time=timedelta(minutes=1)):

    return base_time * (1 + transacoes_recusadas)
