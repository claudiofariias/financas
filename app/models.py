from datetime import date
from app.database import saldo_collection, users_collection
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def save(self):
        users_collection.insert_one({
            "username": self.username,
            "password": self.password_hash
        })

    @staticmethod
    def find_by_username(username):
        return users_collection.find_one({"username": username})

    @staticmethod
    def check_password(user_password_hash, password):
        return check_password_hash(user_password_hash, password)

class Saldo:
    def __init__(self, username):
        self.username = username
        self.data = saldo_collection.find_one({"username": username}) or {
            "username": username,
            "valor": 0,
            "salario": 0,
            "parcelas": [],
            "despesas": [],
            "receitas": [],
            "salarios_recebidos": [],
        }

    def salvar(self):
        saldo_collection.update_one({"username": self.username}, {"$set": self.data}, upsert=True)

    def adicionar_parcela(self, valor, parcelas, mes_inicio, descricao):
        hoje = date.today()
        valor_parcela = valor / parcelas
        import uuid

        transacao_id = str(uuid.uuid4())

        # Adiciona a despesa ao histórico (sem afetar o saldo)
        self.data["despesas"].append({
            "id": transacao_id,
            "valor": valor,
            "categoria": "Compra Parcelada",
            "descricao": f"{descricao} ({parcelas}x de R$ {valor_parcela:,.2f})",
            "tipo": "despesa",
            "parcelas": parcelas
        })

        for i in range(parcelas):
            mes = (mes_inicio + i - 1) % 12 + 1
            ano = hoje.year + ((mes_inicio + i - 1) // 12)

            # Apenas desconta do saldo se for o mês atual
            if mes == hoje.month and ano == hoje.year:
                self.data["valor"] -= valor_parcela
            
            self.data["parcelas"].append({
                "transacao_id": transacao_id,
                "descricao": descricao,
                "valor": valor_parcela,
                "mes": mes,
                "ano": ano
            })

        self.salvar()
    
    def adicionar_despesa(self, valor, categoria, descricao=""):
        self.data["valor"] -= valor
        import uuid
        self.data["despesas"].append({
            "id": str(uuid.uuid4()),
            "valor": valor,
            "categoria": categoria,
            "descricao": descricao,
            "tipo": "despesa"
        })
        self.salvar()

    def adicionar_receita(self, valor, categoria, descricao=""):
        self.data["valor"] += valor
        import uuid
        self.data["receitas"].append({
            "id": str(uuid.uuid4()),
            "valor": valor,
            "categoria": categoria,
            "descricao": descricao,
            "tipo": "receita"
        })
        self.salvar()


    def limpar(self):
        saldo_collection.delete_many({})
        self.data = {
            "valor": 0,
            "salario": 0,
            "parcelas": [],
            "despesas": [],
            "receitas": [],
            "salarios_recebidos": [],
        }

    def get_transacao(self, transacao_id):
        for transacao in self.data["despesas"]:
            if transacao["id"] == transacao_id:
                return transacao
        for transacao in self.data["receitas"]:
            if transacao["id"] == transacao_id:
                return transacao
        return None

    def editar_transacao(self, transacao_id, valor, categoria, descricao, num_parcelas=None):
        import re
        transacao_original = self.get_transacao(transacao_id)

        if not transacao_original:
            return

        # Se não for compra parcelada, usa a lógica simples
        if transacao_original.get("categoria") != "Compra Parcelada":
            lista_transacoes = None
            if transacao_original["tipo"] == "despesa":
                lista_transacoes = self.data["despesas"]
                self.data["valor"] += transacao_original["valor"]
                self.data["valor"] -= valor
            elif transacao_original["tipo"] == "receita":
                lista_transacoes = self.data["receitas"]
                self.data["valor"] -= transacao_original["valor"]
                self.data["valor"] += valor
            
            if lista_transacoes is not None:
                for transacao in lista_transacoes:
                    if transacao["id"] == transacao_id:
                        transacao["valor"] = valor
                        transacao["categoria"] = categoria
                        transacao["descricao"] = descricao
                        break
            self.salvar()
            return

        # --- Tratamento para Compra Parcelada ---

        # 1. Limpa a descrição para remover o texto da parcela antiga
        clean_descricao = re.sub(r'\s\(\d+x de R\$ [0-9,.]+\)$', '', descricao)

        # 2. Guarda os dados necessários da transação original
        #    Usa o novo número de parcelas se for fornecido, senão mantém o antigo.
        novo_num_parcelas = num_parcelas if num_parcelas is not None else transacao_original["parcelas"]
        
        parcelas_originais = [p for p in self.data["parcelas"] if p.get("transacao_id") == transacao_id]
        
        if not parcelas_originais:
            self.excluir_transacao(transacao_id)
            self.adicionar_despesa(valor, categoria, clean_descricao)
            return

        primeira_parcela = min(parcelas_originais, key=lambda x: (x["ano"], x["mes"]))
        mes_inicio = primeira_parcela["mes"]

        # 3. Exclui a transação antiga completamente
        self.excluir_transacao(transacao_id)

        # 4. Adiciona a nova transação parcelada com os dados corretos
        self.adicionar_parcela(valor, novo_num_parcelas, mes_inicio, clean_descricao)

    def limpar_parcelas(self):
        self.data["parcelas"] = []
        self.salvar()

    def excluir_transacao(self, transacao_id):
        hoje = date.today()
        transacao_encontrada = None
        for transacao in self.data["despesas"]:
            if transacao["id"] == transacao_id:
                transacao_encontrada = transacao
                break

        if transacao_encontrada:
            # Se for compra parcelada, ajusta o saldo corretamente
            if transacao_encontrada.get("categoria") == "Compra Parcelada":
                valor_total = transacao_encontrada["valor"]
                num_parcelas = transacao_encontrada["parcelas"]
                valor_parcela = valor_total / num_parcelas

                # Verifica se alguma parcela já foi paga no mês atual
                parcela_paga_mes_atual = any(
                    p["mes"] == hoje.month and p["ano"] == hoje.year
                    for p in self.data["parcelas"]
                    if p.get("transacao_id") == transacao_id
                )

                if parcela_paga_mes_atual:
                    self.data["valor"] += valor_parcela

                # Remove a transação principal e as parcelas futuras
                self.data["despesas"].remove(transacao_encontrada)
                self.data["parcelas"] = [
                    p for p in self.data["parcelas"]
                    if p.get("transacao_id") != transacao_id
                ]
            else:
                # Para despesas normais, restitui o valor total
                self.data["valor"] += transacao_encontrada["valor"]
                self.data["despesas"].remove(transacao_encontrada)

            self.salvar()
            return
        for transacao in self.data["receitas"]:
            if transacao["id"] == transacao_id:
                self.data["valor"] -= transacao["valor"]
                self.data["receitas"].remove(transacao)
                self.salvar()
                return

