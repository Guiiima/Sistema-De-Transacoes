from random import choices

def validar_seletor(transacao, validadores_disponiveis):
    total_saldo = sum(v['saldo'] for v in validadores_disponiveis.values())
    probabilidades = {}

    for id_validador, validador in validadores_disponiveis.items():
        chance_base = validador['saldo'] / total_saldo
        if validador['flag'] == 1:
            chance = chance_base * 0.5
        elif validador['flag'] == 2:
            chance = chance_base * 0.25
        else:
            chance = chance_base

        probabilidades[id_validador] = min(chance, 0.20)

    ids_validadores = list(probabilidades.keys())
    pesos = list(probabilidades.values())

    selecionados = choices(ids_validadores, pesos, k=3)

    return selecionados
