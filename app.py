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
    Escola,
    Usuario,
    Turma,
    #UsuarioTurma,
    Estudante,
    RegistroSaudeMental
)

import os


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    }), 200

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
# API — ESCOLAS
# ============================================================

@app.route("/api/escolas", methods=["GET"])
def listar_escolas():

    escolas = Escola.query.filter_by(
        ativo=True
    ).order_by(
        Escola.nome
    ).all()

    return jsonify([
        escola.to_dict()
        for escola in escolas
    ])


@app.route("/api/escolas/<int:escola_id>", methods=["GET"])
def obter_escola(escola_id):

    escola = Escola.query.get(escola_id)

    if not escola:
        return jsonify({
            "sucesso": False,
            "mensagem": "Escola não encontrada."
        }), 404

    return jsonify({
        "sucesso": True,
        "escola": escola.to_dict()
    })


# ============================================================
# API — USUÁRIOS
# ============================================================
@app.route("/api/cadastro", methods=["POST"])
def cadastrar():

    dados = request.get_json()

    if not dados:
        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

    # --------------------------------------------------------
    # Validação básica
    # --------------------------------------------------------

    campos_obrigatorios = [
        "nome",
        "email",
        "telefone",
        "perfil",
        "matricula",
        "estado",
        "municipio",
        "senha"
    ]

    for campo in campos_obrigatorios:

        if not dados.get(campo):

            return jsonify({
                "sucesso": False,
                "mensagem": f"O campo '{campo}' é obrigatório."
            }), 400

    # --------------------------------------------------------
    # Verificar se o e-mail já está cadastrado
    # --------------------------------------------------------

    usuario_existente = Usuario.query.filter_by(
        email=dados["email"]
    ).first()

    if usuario_existente:

        return jsonify({
            "sucesso": False,
            "mensagem": "E-mail já cadastrado."
        }), 400

    # --------------------------------------------------------
    # ESCOLA AMPARA
    #
    # Por enquanto o sistema possui apenas uma escola.
    # O vínculo é definido pelo banco e não pelo formulário.
    # --------------------------------------------------------

    escola = Escola.query.get(1)

    if not escola:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "A Escola Ampara não foi encontrada "
                "no banco de dados."
            )
        }), 500

    # --------------------------------------------------------
    # Criar usuário
    # --------------------------------------------------------

    usuario = Usuario(
        nome=dados["nome"],
        email=dados["email"],
        telefone=dados["telefone"],
        perfil=dados["perfil"],
        matricula=dados["matricula"],
        estado=dados["estado"],
        municipio=dados["municipio"],

        # Mantemos o campo antigo por compatibilidade
        escola=escola.nome,

        # Novo relacionamento com a tabela escolas
        escola_id=escola.id,

        senha_hash=generate_password_hash(
            dados["senha"]
        ),

        validado=False
    )

    db.session.add(usuario)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": "Cadastro enviado.",
        "usuario": {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "perfil": usuario.perfil,
            "escola": escola.nome,
            "escola_id": escola.id
        }
    }), 201
# ==========================
# FIM API/CADASTRO USUÁRIO
# ==========================

@app.route("/api/login", methods=["POST"])
def login():

    dados = request.get_json()

    if not dados:
        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

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
            ) as arquivo:

                creds = json.load(arquivo)

                if email_input in creds:

                    user_info = creds[email_input]

                    if user_info.get(
                        "senha"
                    ) == senha_input:

                        return jsonify({
                            "sucesso": True,
                            "usuario": {
                                "nome": user_info.get(
                                    "nome"
                                ),
                                "email": email_input,
                                "perfil": user_info.get(
                                    "perfil"
                                ),
                                "escola": user_info.get(
                                    "escola"
                                )
                            }
                        })

                    return jsonify({
                        "sucesso": False,
                        "mensagem": "Senha inválida."
                    }), 401

        except Exception as erro:

            print(
                "Erro ao carregar "
                f"credentials.json: {erro}"
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

    escola_id = request.args.get(
        "escola_id",
        type=int
    )

    consulta = Usuario.query

    if escola_id:
        consulta = consulta.filter_by(
            escola_id=escola_id
        )

    usuarios = consulta.order_by(
        Usuario.nome
    ).all()

    return jsonify([
        usuario.to_dict()
        for usuario in usuarios
    ])


@app.route(
    "/api/aprovar/<int:id>",
    methods=["GET"]
)
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

@app.route(
    "/api/turmas",
    methods=["POST"]
)
def criar_turma():

    dados = request.get_json()

    if not dados:
        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

    nome = dados.get("nome")
    ano = dados.get("ano")

    escola_id = dados.get(
        "escola_id"
    )

    # Compatibilidade com frontend antigo
    escola_nome = dados.get(
        "escola"
    )

    usuario_id = dados.get(
        "usuario_id"
    )

    # --------------------------------------------------------
    # Validação
    # --------------------------------------------------------

    if not nome or not ano:
        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Nome e ano são obrigatórios."
            )
        }), 400

    # --------------------------------------------------------
    # Localizar escola
    # --------------------------------------------------------

    escola = None

    if escola_id:

        escola = Escola.query.get(
            escola_id
        )

        if not escola:

            return jsonify({
                "sucesso": False,
                "mensagem": "Escola não encontrada."
            }), 404

    elif escola_nome:

        escola = Escola.query.filter_by(
            nome=escola_nome
        ).first()

        if not escola:

            return jsonify({
                "sucesso": False,
                "mensagem": "Escola não encontrada."
            }), 404

    else:

        return jsonify({
            "sucesso": False,
            "mensagem": "Escola é obrigatória."
        }), 400

    # --------------------------------------------------------
    # Verificar usuário, se informado
    # --------------------------------------------------------

    usuario = None

    if usuario_id:

        usuario = Usuario.query.get(
            usuario_id
        )

        if not usuario:

            return jsonify({
                "sucesso": False,
                "mensagem": (
                    "Usuário não encontrado."
                )
            }), 404

        # Usuário e turma devem pertencer
        # à mesma escola.

        if usuario.escola_id != escola.id:

            return jsonify({
                "sucesso": False,
                "mensagem": (
                    "O usuário não pertence "
                    "à escola informada."
                )
            }), 400

    # --------------------------------------------------------
    # Criar turma
    # --------------------------------------------------------

    turma = Turma(
        nome=nome,
        ano=int(ano),

        # Campo antigo mantido temporariamente
        escola=escola.nome,

        # Novo relacionamento
        escola_id=escola.id,

        # Mantido apenas para compatibilidade
        usuario_id=usuario_id
    )

    db.session.add(turma)
    db.session.flush()

    # --------------------------------------------------------
    # Se houver usuário responsável, criar vínculo
    # na tabela usuarios_turmas.
    # --------------------------------------------------------

    if usuario:

        vinculo = UsuarioTurma(
            usuario_id=usuario.id,
            turma_id=turma.id
        )

        db.session.add(vinculo)

    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": "Turma criada com sucesso.",
        "turma": turma.to_dict()
    }), 201


@app.route(
    "/api/turmas",
    methods=["GET"]
)
def listar_turmas():

    escola_id = request.args.get(
        "escola_id",
        type=int
    )

    consulta = Turma.query

    if escola_id:

        consulta = consulta.filter_by(
            escola_id=escola_id
        )

    turmas = consulta.order_by(
        Turma.ano,
        Turma.nome
    ).all()

    return jsonify([
        turma.to_dict()
        for turma in turmas
    ])


@app.route(
    "/api/turmas/<int:turma_id>",
    methods=["GET"]
)
def obter_turma(turma_id):

    turma = Turma.query.get(
        turma_id
    )

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
# API — USUÁRIOS ↔ TURMAS
# ============================================================

@app.route(
    "/api/turmas/<int:turma_id>/usuarios",
    methods=["POST"]
)
def vincular_usuario_turma(
    turma_id
):

    dados = request.get_json()

    if not dados:

        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

    usuario_id = dados.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "sucesso": False,
            "mensagem": "usuario_id é obrigatório."
        }), 400

    turma = Turma.query.get(
        turma_id
    )

    if not turma:

        return jsonify({
            "sucesso": False,
            "mensagem": "Turma não encontrada."
        }), 404

    usuario = Usuario.query.get(
        usuario_id
    )

    if not usuario:

        return jsonify({
            "sucesso": False,
            "mensagem": "Usuário não encontrado."
        }), 404

    # --------------------------------------------------------
    # Verificar se usuário e turma pertencem à mesma escola
    # --------------------------------------------------------

    if (
        turma.escola_id is not None
        and usuario.escola_id is not None
        and turma.escola_id != usuario.escola_id
    ):

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Usuário e turma pertencem "
                "a escolas diferentes."
            )
        }), 400

    # --------------------------------------------------------
    # Verificar vínculo existente
    # --------------------------------------------------------

    vinculo_existente = UsuarioTurma.query.filter_by(
        usuario_id=usuario_id,
        turma_id=turma_id
    ).first()

    if vinculo_existente:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Usuário já está vinculado à turma."
            )
        }), 400

    # --------------------------------------------------------
    # Criar vínculo
    # --------------------------------------------------------

    vinculo = UsuarioTurma(
        usuario_id=usuario_id,
        turma_id=turma_id
    )

    db.session.add(vinculo)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": (
            "Usuário vinculado à turma."
        ),
        "vinculo": vinculo.to_dict()
    }), 201


@app.route(
    "/api/turmas/<int:turma_id>/usuarios",
    methods=["GET"]
)
def listar_usuarios_turma(turma_id):

    turma = Turma.query.get(
        turma_id
    )

    if not turma:

        return jsonify({
            "sucesso": False,
            "mensagem": "Turma não encontrada."
        }), 404

    vinculos = UsuarioTurma.query.filter_by(
        turma_id=turma_id
    ).all()

    usuarios = [
        vinculo.usuario.to_dict()
        for vinculo in vinculos
        if vinculo.usuario
    ]

    return jsonify({
        "sucesso": True,
        "turma": turma.to_dict(),
        "usuarios": usuarios
    })


@app.route(
    "/api/turmas/<int:turma_id>/usuarios/<int:usuario_id>",
    methods=["DELETE"]
)
def remover_usuario_turma(
    turma_id,
    usuario_id
):

    vinculo = UsuarioTurma.query.filter_by(
        turma_id=turma_id,
        usuario_id=usuario_id
    ).first()

    if not vinculo:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Vínculo não encontrado."
            )
        }), 404

    db.session.delete(vinculo)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": (
            "Usuário removido da turma."
        )
    })


# ============================================================
# API — ESTUDANTES
# ============================================================

@app.route(
    "/api/estudantes",
    methods=["POST"]
)
def criar_estudante():

    dados = request.get_json()

    if not dados:

        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

    nome = dados.get(
        "nome"
    )

    matricula = dados.get(
        "matricula"
    )

    turma_id = dados.get(
        "turma_id"
    )

    if not nome or not turma_id:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Nome e turma são obrigatórios."
            )
        }), 400

    turma = Turma.query.get(
        turma_id
    )

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
        "mensagem": (
            "Estudante cadastrado com sucesso."
        ),
        "estudante": estudante.to_dict()
    }), 201


@app.route(
    "/api/turmas/<int:turma_id>/estudantes",
    methods=["GET"]
)
def listar_estudantes_turma(
    turma_id
):

    turma = Turma.query.get(
        turma_id
    )

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


@app.route(
    "/api/estudantes/<int:estudante_id>",
    methods=["GET"]
)
def obter_estudante(
    estudante_id
):

    estudante = Estudante.query.get(
        estudante_id
    )

    if not estudante:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Estudante não encontrado."
            )
        }), 404

    return jsonify({
        "sucesso": True,
        "estudante": estudante.to_dict()
    })


# ============================================================
# API — REGISTROS DE SAÚDE MENTAL
# ============================================================

@app.route(
    "/api/registros",
    methods=["POST"]
)
def criar_registro():

    dados = request.get_json()

    if not dados:

        return jsonify({
            "sucesso": False,
            "mensagem": "Dados não enviados."
        }), 400

    estudante_id = dados.get(
        "estudante_id"
    )

    usuario_id = dados.get(
        "usuario_id"
    )

    tipo = dados.get(
        "tipo"
    )

    gravidade = dados.get(
        "gravidade"
    )

    descricao = dados.get(
        "descricao"
    )

    # --------------------------------------------------------
    # Validação
    # --------------------------------------------------------

    if not estudante_id:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Estudante é obrigatório."
            )
        }), 400

    if not usuario_id:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Usuário responsável é obrigatório."
            )
        }), 400

    if not tipo:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Tipo da situação é obrigatório."
            )
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
            "mensagem": (
                "Estudante não encontrado."
            )
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
            "mensagem": (
                "Usuário não encontrado."
            )
        }), 404

    # --------------------------------------------------------
    # Verificar escola
    #
    # O usuário que registra uma situação deve pertencer
    # à mesma escola do estudante.
    # --------------------------------------------------------

    turma = estudante.turma

    if (
        usuario.escola_id is not None
        and turma
        and turma.escola_id is not None
        and usuario.escola_id != turma.escola_id
    ):

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "O usuário não pertence "
                "à escola do estudante."
            )
        }), 403

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
        "mensagem": (
            "Registro criado com sucesso."
        ),
        "registro": registro.to_dict()
    }), 201


@app.route(
    "/api/estudantes/<int:estudante_id>/historico",
    methods=["GET"]
)
def historico_estudante(
    estudante_id
):

    estudante = Estudante.query.get(
        estudante_id
    )

    if not estudante:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Estudante não encontrado."
            )
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

        "quantidade_registros": len(
            registros
        ),

        "historico": [
            registro.to_dict()
            for registro in registros
        ]
    })


@app.route(
    "/api/estudantes/<int:estudante_id>/registros",
    methods=["GET"]
)
def listar_registros_estudante(
    estudante_id
):

    estudante = Estudante.query.get(
        estudante_id
    )

    if not estudante:

        return jsonify({
            "sucesso": False,
            "mensagem": (
                "Estudante não encontrado."
            )
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
