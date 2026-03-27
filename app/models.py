from datetime import date
from app.database import saldo_collection, users_collection
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, email, password):
        self.email = email
        self.password_hash = generate_password_hash(password)

    def save(self):
        users_collection.insert_one({
            "email": self.email,
            "password": self.password_hash
        })

    @staticmethod
    def find_by_email(email):
        return users_collection.find_one({"email": email})

    @staticmethod
    def check_password(user_password_hash, password):
        return check_password_hash(user_password_hash, password)

class Saldo:
    def __init__(self, user_email):
        self.user_email = user_email
        self.data = saldo_collection.find_one({"user_email": user_email}) or {
            "user_email": user_email,
            "valor": 0,
            "salario": 0,
            "parcelas": [],
            "despesas": [],
            "receitas": [],
            "salarios_recebidos": [],
            "initial_setup_done": False
        }

    def salvar(self):
        saldo_collection.update_one({"user_email": self.user_email}, {"$set": self.data}, upsert=True)

    def adicionar_parcela(self, valor, parcelas, mes_inicio):
        hoje = date.today()
        valor_parcela = valor / parcelas

        for i in range(parcelas):
            mes = (mes_inicio + i - 1) % 12 + 1
            ano = hoje.year + ((mes_inicio + i - 1) // 12)

            self.data["parcelas"].append({
                "valor": valor_parcela,
                "mes": mes,
                "ano": ano
            })

        self.salvar()
    
    def definir_saldo_inicial(self, valor):
        self.data["valor"] = valor
        self.data["initial_setup_done"] = True
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
            "initial_setup_done": False
        }

    def get_transacao(self, transacao_id):
        for transacao in self.data["despesas"]:
            if transacao["id"] == transacao_id:
                return transacao
        for transacao in self.data["receitas"]:
            if transacao["id"] == transacao_id:
                return transacao
        return None

    def editar_transacao(self, transacao_id, valor, categoria, descricao):
        for transacao in self.data["despesas"]:
            if transacao["id"] == transacao_id:
                self.data["valor"] += transacao["valor"]
                transacao["valor"] = valor
                transacao["categoria"] = categoria
                transacao["descricao"] = descricao
                self.data["valor"] -= valor
                self.salvar()
                return
        for transacao in self.data["receitas"]:
            if transacao["id"] == transacao_id:
                self.data["valor"] -= transacao["valor"]
                transacao["valor"] = valor
                transacao["categoria"] = categoria
                transacao["descricao"] = descricao
                self.data["valor"] += valor
                self.salvar()
                return

    def limpar_parcelas(self):
        self.data["parcelas"] = []
        self.salvar()

    def excluir_transacao(self, transacao_id):
        for transacao in self.data["despesas"]:
            if transacao["id"] == transacao_id:
                self.data["valor"] += transacao["valor"]
                self.data["despesas"].remove(transacao)
                self.salvar()
                return
        for transacao in self.data["receitas"]:
            if transacao["id"] == transacao_id:
                self.data["valor"] -= transacao["valor"]
                self.data["receitas"].remove(transacao)
                self.salvar()
                return

