from flask import Blueprint, render_template, request, redirect, session, flash
from app.models import Saldo, User
from app.services import calcular_projecao, Mes, CategoriaReceita, CategoriaDespesa

bp = Blueprint("main", __name__)


# 🔹 DASHBOARD
@bp.route("/")
def index():
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])

    if not saldo.data.get("initial_setup_done"):
        return redirect("/setup")

    despesas = saldo.data.get("despesas", [])
    receitas = saldo.data.get("receitas", [])
    historico = sorted(despesas + receitas, key=lambda x: x.get('data', ''), reverse=True)
    return render_template("index.html", saldo=saldo.data, historico=historico)


# 🔹 SETUP INICIAL
@bp.route("/setup", methods=["GET", "POST"])
def setup():
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        tem_salario = request.form.get("tem_salario") == "on"
        salario = float(request.form.get("salario") or 0) if tem_salario else 0

        saldo.definir_saldo_inicial(valor)

        return redirect("/")

    return render_template("setup.html")




# 🔹 RECEITA
@bp.route("/receita", methods=["GET", "POST"])
def receita():
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        saldo.adicionar_receita(valor)

        return redirect("/")

    return render_template("receita.html")


# 🔹 DESPESA
@bp.route("/despesa", methods=["GET", "POST"])
def despesa():
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        saldo.adicionar_despesa(valor)

        return redirect("/")

    return render_template("despesa.html")


# 🔹 PARCELAS
@bp.route("/parcelas", methods=["GET", "POST"])
def parcelas():
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        parcelas = int(request.form["parcelas"])
        mes = int(request.form["mes"])

        saldo.adicionar_parcela(valor, parcelas, mes)

        return redirect("/")

    return render_template("parcelas.html", saldo=saldo.data, meses=Mes)


# 🔹 LISTA DE PARCELAS
@bp.route("/parcelas/lista")
def lista_parcelas():
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])
    return render_template("lista_parcelas.html", parcelas=saldo.data.get("parcelas", []))



@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.find_by_email(email)

        if user and User.check_password(user["password"], password):
            session["user_email"] = email
            return redirect("/")
        else:
            flash("Email ou senha inválidos.")

    return render_template("login.html")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if User.find_by_email(email):
            flash("Este email já está em uso.")
        else:
            user = User(email, password)
            user.save()
            flash("Conta criada com sucesso!")
            return redirect("/login")

    return render_template("register.html")

@bp.route("/logout")
def logout():
    session.pop("user_email", None)
    return redirect("/login")

@bp.route("/movimentacao", methods=["GET", "POST"])
def movimentacao():
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])

    if request.method == "POST":
        tipo = request.form["tipo"]
        valor = float(request.form["valor"])
        categoria = request.form["categoria"]
        descricao = request.form["descricao"]

        if tipo == "receita":
            saldo.adicionar_receita(valor, categoria, descricao)
        else:
            saldo.adicionar_despesa(valor, categoria, descricao)

        return redirect("/")

    categorias_receita_dict = {cat.name: cat.value for cat in CategoriaReceita}
    categorias_despesa_dict = {cat.name: cat.value for cat in CategoriaDespesa}
    return render_template("movimentacao.html", saldo=saldo.data, categorias_receita=categorias_receita_dict, categorias_despesa=categorias_despesa_dict)

@bp.route("/faturas")
def faturas():
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])
    projecao = calcular_projecao(saldo.data)

    # Adiciona o nome do mês na projeção
    for p in projecao:
        p["mes_nome"] = Mes(p["mes"]).name.capitalize()

    return render_template("faturas.html", saldo=saldo.data, projecao=projecao)

@bp.route("/editar_transacao/<transacao_id>", methods=["GET", "POST"])
def editar_transacao(transacao_id):
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        categoria = request.form["categoria"]
        descricao = request.form["descricao"]
        saldo.editar_transacao(transacao_id, valor, categoria, descricao)
        return redirect("/")
    
    @bp.route("/limpar_parcelas")
    def limpar_parcelas():
        if "user_email" not in session:
            return redirect("/login")
    
        saldo = Saldo(session["user_email"])
        saldo.limpar_parcelas()
        return redirect("/faturas")
    
    @bp.route("/limpar_dados")
    def limpar_dados():
        if "user_email" not in session:
            return redirect("/login")
    
        saldo = Saldo(session["user_email"])
        saldo.limpar()
        return redirect("/")

    transacao = saldo.get_transacao(transacao_id)
    return render_template("editar_transacao.html", transacao=transacao)

@bp.route("/excluir_transacao/<transacao_id>")
def excluir_transacao(transacao_id):
    if "user_email" not in session:
        return redirect("/login")

    saldo = Saldo(session["user_email"])
    saldo.excluir_transacao(transacao_id)
    return redirect("/")

