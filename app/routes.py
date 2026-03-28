from flask import Blueprint, render_template, request, redirect, session, flash
from app.models import Saldo, User
from app.services import calcular_projecao, Mes, CategoriaReceita, CategoriaDespesa

bp = Blueprint("main", __name__)


# 🔹 DASHBOARD
@bp.route("/")
def index():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])

    despesas = saldo.data.get("despesas", [])
    receitas = saldo.data.get("receitas", [])
    historico = sorted(despesas + receitas, key=lambda x: x.get('data', ''), reverse=True)
    return render_template("index.html", saldo=saldo.data, historico=historico)


# 🔹 SETUP INICIAL
# 🔹 RECEITA
@bp.route("/receita", methods=["GET", "POST"])
def receita():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        saldo.adicionar_receita(valor)

        return redirect("/")

    return render_template("receita.html")


# 🔹 DESPESA
@bp.route("/despesa", methods=["GET", "POST"])
def despesa():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        saldo.adicionar_despesa(valor)

        return redirect("/")

    return render_template("despesa.html")


# 🔹 PARCELAS
@bp.route("/parcelas", methods=["GET", "POST"])
def parcelas():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        parcelas = int(request.form["parcelas"])
        mes = int(request.form["mes"])
        descricao = request.form["descricao"]

        saldo.adicionar_parcela(valor, parcelas, mes, descricao)

        return redirect("/")

    return render_template("parcelas.html", saldo=saldo.data, meses=Mes)


# 🔹 LISTA DE PARCELAS
@bp.route("/parcelas/lista")
def lista_parcelas():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])
    return render_template("lista_parcelas.html", parcelas=saldo.data.get("parcelas", []))



@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.find_by_username(username)

        if user and User.check_password(user["password"], password):
            session["username"] = username
            return redirect("/")
        else:
            flash("Usuário ou senha inválidos.")

    return render_template("login.html")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.find_by_username(username):
            flash("Este nome de usuário já está em uso.")
        else:
            user = User(username, password)
            user.save()
            flash("Conta criada com sucesso!")
            return redirect("/login")

    return render_template("register.html")

@bp.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")

@bp.route("/movimentacao", methods=["GET", "POST"])
def movimentacao():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])

    tipo = request.args.get("tipo", "receita")  # 👈 PEGA DA URL

    if request.method == "POST":
        tipo = request.form["tipo"]  # 👈 vem do hidden input
        valor = float(request.form["valor"])
        categoria = request.form["categoria"]
        descricao = request.form["descricao"]

        if tipo == "receita":
            saldo.adicionar_receita(valor, categoria, descricao)
        else:
            saldo.adicionar_despesa(valor, categoria, descricao)

        return redirect("/")

    categorias_receita_dict = {cat.value: cat.value for cat in CategoriaReceita}
    categorias_despesa_dict = {cat.value: cat.value for cat in CategoriaDespesa}

    return render_template(
        "movimentacao.html",
        saldo=saldo.data,
        categorias_receita=categorias_receita_dict,
        categorias_despesa=categorias_despesa_dict,
        tipo=tipo
    )
@bp.route("/faturas")
def faturas():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])
    projecao = calcular_projecao(saldo.data)

    # Adiciona o nome do mês na projeção
    for p in projecao:
        p["mes_nome"] = Mes(p["mes"]).name.capitalize()

    return render_template("faturas.html", saldo=saldo.data, projecao=projecao)

@bp.route("/editar_transacao/<transacao_id>", methods=["GET", "POST"])
def editar_transacao(transacao_id):
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])

    if request.method == "POST":
        valor = float(request.form["valor"])
        categoria = request.form["categoria"]
        descricao = request.form["descricao"]
        saldo.editar_transacao(transacao_id, valor, categoria, descricao)
        return redirect("/")
    
    saldo_instance = Saldo(session["username"])
    transacao = saldo_instance.get_transacao(transacao_id)
    
    if transacao is None:
        flash("Transação não encontrada.")
        return redirect("/")

    return render_template("editar_transacao.html", transacao=transacao)

@bp.route("/limpar_parcelas")
def limpar_parcelas():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])
    saldo.limpar_parcelas()
    return redirect("/faturas")

@bp.route("/limpar_dados")
def limpar_dados():
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])
    saldo.limpar()
    return redirect("/")

@bp.route("/excluir_transacao/<transacao_id>")
def excluir_transacao(transacao_id):
    if "username" not in session:
        return redirect("/login")

    saldo = Saldo(session["username"])
    saldo.excluir_transacao(transacao_id)
    return redirect("/")

