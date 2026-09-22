from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from config import Config
from models import (
    db,
    Usuario,
    Turma,
    Estudante,
    RegistroSaudeMental
)

import os

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    }), 200

db.init_app(app)

# ============================================================
# BANCO DE DADOS
# ============================================================

with app.app_context():
    db.create_all()

# ============================================================
# PÁGINAS
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/cadastro_turma")
def cadastro_turma():
    return render_template("cadastro_turma.html")

@app.route("/cadastro_estudante")
def cadastro_estudante():
    return render_template("cadastro_estudante.html")

# ============================================================
# API — USUÁRIOS
# ============================================================

@app.route("/api/cadastro", methods=["POST"])
def cadastrar():

    dados = request.json

    db_url = os.environ.get(
        "DATABASE_URL",
        "sqlite:///app.db"
    )

    print(db_url)

    usuario_existente = Usuario.query.filter_by(
        email=dados["email"]
    ).first()

    if usuario_existente:

        return jsonify({
            "sucesso": False,
            "mensagem": "E-mail já cadastrado."
        }), 400

    usuario = Usuario(
        nome=dados["nome"],
        email=dados["email"],
        telefone=dados["telefone"],
        perfil=dados["perfil"],
        matricula=dados["matricula"],
        estado=dados["estado"],
        municipio=dados["municipio"],
        escola=dados["escola"],
        senha_hash=generate_password_hash(
            dados["senha"]
        )
    )

    db.session.add(usuario)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": "Cadastro enviado."
    })


@app.route("/api/login", methods=["POST"])
def login():

    dados = request.json

    email_input = dados.get("email")
    senha_input = dados.get("senha")

    # --------------------------------------------------------
    # 1. credentials.json — simulação de perfis
    # --------------------------------------------------------

    if os.path.exists("credentials.json"):

        try:

            import json

            with open(
                "credentials.json",
                "r",
                encoding="utf-8"
            ) as f:

                creds = json.load(f)

                if email_input in creds:

                    user_info = creds[email_input]

                    if user_info.get("senha") == senha_input:

                        return jsonify({
                            "sucesso": True,
                            "usuario": {
                                "nome": user_info.get("nome"),
                                "email": email_input,
                                "perfil": user_info.get("perfil"),
                                "escola": user_info.get("escola")
                            }
                        })

                    return jsonify({
                        "sucesso": False,
                        "mensagem": "Senha inválida."
                    }), 401

        except Exception as e:

            print(
                f"Erro ao carregar credentials.json: {e}"
            )

    # --------------------------------------------------------
    # 2. Banco de dados
    # --------------------------------------------------------

    usuario = Usuario.query.filter_by(
        email=email_input
    ).first()

    if not usuario:

        return jsonify({
            "sucesso": False,
            "mensagem": "Usuário não encontrado."
        }), 404

    if not check_password_hash(
        usuario.senha_hash,
        senha_input
    ):

        return jsonify({
            "sucesso": False,
            "mensagem": "Senha inválida."
        }), 401

    return jsonify({
        "sucesso": True,
        "usuario": usuario.to_dict()
    })


@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():

    usuarios = Usuario.query.all()

    return jsonify([
        u.to_dict()
        for u in usuarios
    ])


@app.route("/api/aprovar/<int:id>", methods=["GET"])
def aprovar_usuario(id):

    usuario = Usuario.query.get(id)

    if usuario:

        usuario.validado = True

        db.session.commit()

        return jsonify({
            "sucesso": True,
            "mensagem": "Usuário aprovado."
        })

    return jsonify({
        "sucesso": False,
        "mensagem": "Usuário não encontrado."
    }), 404


# ============================================================
# API — TURMAS
# ============================================================

@app.route("/api/turmas", methods=["POST"])
def criar_turma():

    dados = request.get_json()

    if not dados:
        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

    nome = dados.get("nome")
    ano = dados.get("ano")
    escola = dados.get("escola")
    usuario_id = dados.get("usuario_id")

    if not nome or not ano or not escola:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Nome, ano e escola são obrigatórios."
            )
        }), 400

    # Verifica o usuário responsável, caso informado
    usuario = None

    if usuario_id:

        usuario = Usuario.query.get(usuario_id)

        if not usuario:

            return jsonify({
                "sucesso": False,
                "mensagem": (
                    "Usuário responsável não encontrado."
                )
            }), 404

    turma = Turma(
        nome=nome,
        ano=int(ano),
        escola=escola,
        usuario_id=usuario_id
    )

    db.session.add(turma)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": "Turma criada com sucesso.",
        "turma": turma.to_dict()
    }), 201


@app.route("/api/turmas", methods=["GET"])
def listar_turmas():

    escola = request.args.get("escola")

    consulta = Turma.query

    if escola:
        consulta = consulta.filter_by(
            escola=escola
        )

    turmas = consulta.order_by(
        Turma.ano,
        Turma.nome
    ).all()

    return jsonify([
        turma.to_dict()
        for turma in turmas
    ])


@app.route("/api/turmas/<int:turma_id>", methods=["GET"])
def obter_turma(turma_id):

    turma = Turma.query.get(turma_id)

    if not turma:

        return jsonify({
            "sucesso": False,
            "mensagem": "Turma não encontrada."
        }), 404

    return jsonify({
        "sucesso": True,
        "turma": turma.to_dict()
    })


# ============================================================
# API — ESTUDANTES
# ============================================================

@app.route("/api/estudantes", methods=["POST"])
def criar_estudante():

    dados = request.get_json()

    if not dados:

        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

    nome = dados.get("nome")
    matricula = dados.get("matricula")
    turma_id = dados.get("turma_id")

    if not nome or not turma_id:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Nome e turma são obrigatórios."
            )
        }), 400

    turma = Turma.query.get(turma_id)

    if not turma:

        return jsonify({
            "sucesso": False,
            "mensagem": "Turma não encontrada."
        }), 404

    estudante = Estudante(
        nome=nome,
        matricula=matricula,
        turma_id=turma_id
    )

    db.session.add(estudante)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": "Estudante cadastrado com sucesso.",
        "estudante": estudante.to_dict()
    }), 201


@app.route(
    "/api/turmas/<int:turma_id>/estudantes",
    methods=["GET"]
)
def listar_estudantes_turma(turma_id):

    turma = Turma.query.get(turma_id)

    if not turma:

        return jsonify({
            "sucesso": False,
            "mensagem": "Turma não encontrada."
        }), 404

    estudantes = Estudante.query.filter_by(
        turma_id=turma_id
    ).order_by(
        Estudante.nome
    ).all()

    return jsonify([
        estudante.to_dict()
        for estudante in estudantes
    ])


@app.route("/api/estudantes/<int:estudante_id>", methods=["GET"])
def obter_estudante(estudante_id):

    estudante = Estudante.query.get(
        estudante_id
    )

    if not estudante:

        return jsonify({
            "sucesso": False,
            "mensagem": "Estudante não encontrado."
        }), 404

    return jsonify({
        "sucesso": True,
        "estudante": estudante.to_dict()
    })


# ============================================================
# API — REGISTROS DE SAÚDE MENTAL
# ============================================================

@app.route("/api/registros", methods=["POST"])
def criar_registro():

    dados = request.get_json()

    if not dados:

        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

    estudante_id = dados.get("estudante_id")
    usuario_id = dados.get("usuario_id")
    tipo = dados.get("tipo")
    gravidade = dados.get("gravidade")
    descricao = dados.get("descricao")

    # --------------------------------------------------------
    # Validação dos campos obrigatórios
    # --------------------------------------------------------

    if not estudante_id:
        return jsonify({
            "sucesso": False,
            "mensagem": "Estudante é obrigatório."
        }), 400

    if not usuario_id:
        return jsonify({
            "sucesso": False,
            "mensagem": "Usuário responsável é obrigatório."
        }), 400

    if not tipo:
        return jsonify({
            "sucesso": False,
            "mensagem": "Tipo da situação é obrigatório."
        }), 400

    # --------------------------------------------------------
    # Verificar estudante
    # --------------------------------------------------------

    estudante = Estudante.query.get(
        estudante_id
    )

    if not estudante:

        return jsonify({
            "sucesso": False,
            "mensagem": "Estudante não encontrado."
        }), 404

    # --------------------------------------------------------
    # Verificar usuário
    # --------------------------------------------------------

    usuario = Usuario.query.get(
        usuario_id
    )

    if not usuario:

        return jsonify({
            "sucesso": False,
            "mensagem": "Usuário não encontrado."
        }), 404

    # --------------------------------------------------------
    # Criar registro
    # --------------------------------------------------------

    registro = RegistroSaudeMental(
        estudante_id=estudante_id,
        usuario_id=usuario_id,
        tipo=tipo,
        gravidade=gravidade,
        descricao=descricao
    )

    db.session.add(registro)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": "Registro criado com sucesso.",
        "registro": registro.to_dict()
    }), 201


@app.route(
    "/api/estudantes/<int:estudante_id>/historico",
    methods=["GET"]
)
def historico_estudante(estudante_id):

    estudante = Estudante.query.get(
        estudante_id
    )

    if not estudante:

        return jsonify({
            "sucesso": False,
            "mensagem": "Estudante não encontrado."
        }), 404

    registros = RegistroSaudeMental.query.filter_by(
        estudante_id=estudante_id
    ).order_by(
        RegistroSaudeMental.data_registro.desc()
    ).all()

    return jsonify({
        "sucesso": True,
        "estudante": {
            "id": estudante.id,
            "nome": estudante.nome,
            "matricula": estudante.matricula,
            "turma_id": estudante.turma_id
        },
        "quantidade_registros": len(registros),
        "historico": [
            registro.to_dict()
            for registro in registros
        ]
    })


@app.route(
    "/api/estudantes/<int:estudante_id>/registros",
    methods=["GET"]
)
def listar_registros_estudante(estudante_id):

    estudante = Estudante.query.get(
        estudante_id
    )

    if not estudante:

        return jsonify({
            "sucesso": False,
            "mensagem": "Estudante não encontrado."
        }), 404

    registros = RegistroSaudeMental.query.filter_by(
        estudante_id=estudante_id
    ).order_by(
        RegistroSaudeMental.data_registro.desc()
    ).all()

    return jsonify([
        registro.to_dict()
        for registro in registros
    ])


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
