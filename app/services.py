from datetime import date
from enum import Enum

class Mes(Enum):
    JANEIRO = 1
    FEVEREIRO = 2
    MARCO = 3
    ABRIL = 4
    MAIO = 5
    JUNHO = 6
    JULHO = 7
    AGOSTO = 8
    SETEMBRO = 9
    OUTUBRO = 10
    NOVEMBRO = 11
    DEZEMBRO = 12


class CategoriaReceita(Enum):
    SALARIO = "Salário"
    VENDA = "Venda"
    PRESENTE = "Presente"
    OUTROS = "Outros"

class CategoriaDespesa(Enum):
    ALIMENTACAO = "Alimentação"
    MORADIA = "Moradia"
    TRANSPORTE = "Transporte"
    LAZER = "Lazer"
    OUTROS = "Outros"

    def adicionar_despesa(self, valor):
        self.valor -= valor

    def adicionar_receita(self, valor):
        self.valor += valor

    def adicionar_parcela(self, valor, parcelas, mes_inicio):
        hoje = date.today()
        valor_parcela = valor / parcelas

        # aceita Enum ou int
        if isinstance(mes_inicio, Mes):
            mes_inicio = mes_inicio.value

        for i in range(parcelas):
            mes_num = (mes_inicio + i - 1) % 12 + 1
            ano = hoje.year + ((mes_inicio + i - 1) // 12)

            mes_enum = Mes(mes_num)

            if ano == hoje.year and mes_num == hoje.month:
                self.valor -= valor_parcela
            else:
                self.parcelas_futuras.append({
                    "valor": valor_parcela,
                    "mes": mes_enum,
                    "ano": ano
                })

    def processar_mes(self, mes, ano):
        if isinstance(mes, Mes):
            mes = mes.value

        novas = []
        for p in self.parcelas_futuras:
            if p["mes"].value == mes and p["ano"] == ano:
                self.valor -= p["valor"]
            else:
                novas.append(p)

        self.parcelas_futuras = novas

    def listar_parcelas(self):
        for p in self.parcelas_futuras:
            print(f'{p["mes"].name}/{p["ano"]} - R$ {p["valor"]:.2f}')


def calcular_projecao(saldo_data, meses=12):
    from datetime import date

    hoje = date.today()
    saldo_atual = saldo_data.get("valor", 0)
    projecao = []
    
    salarios_recebidos = saldo_data.get("salarios_recebidos", [])
    
    salario_recebido_mes_atual = next((s["valor"] for s in salarios_recebidos if s["mes"] == hoje.month and s["ano"] == hoje.year), 0)
    
    saldo_futuro = saldo_atual - salario_recebido_mes_atual

    salarios_planejados = saldo_data.get("salarios_planejados", [])

    for i in range(meses):
        mes = (hoje.month + i - 1) % 12 + 1
        ano = hoje.year + ((hoje.month + i - 1) // 12)

        salario_planejado = next(
            (s["valor"] for s in salarios_planejados if s["mes"] == mes and s["ano"] == ano),
            saldo_data.get("salario", 0)
        )
        
        saldo_futuro += salario_planejado

        parcelas_mes = []
        for p in saldo_data.get("parcelas", []):
            if p["mes"] == mes and p["ano"] == ano:
                saldo_futuro -= p["valor"]
                parcelas_mes.append(p)
        
        salario_recebido = next(
            (s["valor"] for s in salarios_recebidos if s["mes"] == mes and s["ano"] == ano),
            0
        )

        projecao.append({
            "mes": mes,
            "ano": ano,
            "saldo": round(saldo_futuro, 2),
            "salario_planejado": salario_planejado,
            "salario_recebido": salario_recebido,
            "parcelas": parcelas_mes
        })

    return projecao