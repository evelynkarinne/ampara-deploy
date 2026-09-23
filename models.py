from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ============================================================
# ESCOLA
# ============================================================

class Escola(db.Model):
    __tablename__ = "escolas"

    id = db.Column(
        db.BigInteger,
        primary_key=True
    )

    nome = db.Column(
        db.String(200),
        nullable=False
    )

    codigo_inep = db.Column(
        db.String(20),
        nullable=True
    )

    estado = db.Column(
        db.String(50),
        nullable=True
    )

    municipio = db.Column(
        db.String(100),
        nullable=True
    )

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ========================================================
    # RELACIONAMENTOS
    # ========================================================

    usuarios = db.relationship(
        "Usuario",
        back_populates="escola_relacao",
        foreign_keys="Usuario.escola_id"
    )

    turmas = db.relationship(
        "Turma",
        back_populates="escola_relacao",
        foreign_keys="Turma.escola_id"
    )

    # ========================================================
    # CONVERSÃO PARA JSON
    # ========================================================

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "codigo_inep": self.codigo_inep,
            "estado": self.estado,
            "municipio": self.municipio,
            "ativo": self.ativo,
            "data_cadastro": (
                self.data_cadastro.isoformat()
                if self.data_cadastro
                else None
            )
        }


# ============================================================
# USUÁRIO
# ============================================================

class Usuario(db.Model):
    __tablename__ = "usuarios"

    __table_args__ = {
        "extend_existing": True
    }

    id = db.Column(
        db.BigInteger,
        primary_key=True
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    telefone = db.Column(
        db.String(20)
    )

    perfil = db.Column(
        db.String(30)
    )

    matricula = db.Column(
        db.String(50)
    )

    estado = db.Column(
        db.String(50)
    )

    municipio = db.Column(
        db.String(100)
    )

    # --------------------------------------------------------
    # CAMPO ANTIGO
    # Mantido temporariamente para compatibilidade.
    # --------------------------------------------------------

    escola = db.Column(
        db.String(200)
    )

    # --------------------------------------------------------
    # NOVO RELACIONAMENTO COM ESCOLA
    # --------------------------------------------------------

    escola_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "escolas.id",
            ondelete="RESTRICT"
        ),
        nullable=True
    )

    senha_hash = db.Column(
        db.Text,
        nullable=False
    )

    validado = db.Column(
        db.Boolean,
        default=False
    )

    # ========================================================
    # RELACIONAMENTOS
    # ========================================================

    # Escola à qual o usuário pertence
    escola_relacao = db.relationship(
        "Escola",
        back_populates="usuarios",
        foreign_keys=[escola_id]
    )

    # --------------------------------------------------------
    # RELACIONAMENTO ANTIGO COM TURMAS
    # Mantido temporariamente para compatibilidade.
    # --------------------------------------------------------

    turmas = db.relationship(
        "Turma",
        back_populates="responsavel",
        foreign_keys="Turma.usuario_id"
    )

    # --------------------------------------------------------
    # NOVO RELACIONAMENTO COM TURMAS
    # através de usuarios_turmas
    # --------------------------------------------------------

    vinculos_turmas = db.relationship(
        "UsuarioTurma",
        back_populates="usuario",
        cascade="all, delete-orphan"
    )

    # Registros de saúde mental realizados pelo usuário
    registros_saude_mental = db.relationship(
        "RegistroSaudeMental",
        back_populates="usuario",
        foreign_keys="RegistroSaudeMental.usuario_id"
    )

    # ========================================================
    # CONVERSÃO PARA JSON
    # ========================================================

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "perfil": self.perfil,
            "escola": self.escola,
            "escola_id": self.escola_id,
            "validado": self.validado
        }


# ============================================================
# TURMA
# ============================================================

class Turma(db.Model):
    __tablename__ = "turmas"

    id = db.Column(
        db.BigInteger,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    ano = db.Column(
        db.Integer,
        nullable=False
    )

    # --------------------------------------------------------
    # CAMPO ANTIGO
    # Mantido temporariamente para compatibilidade.
    # --------------------------------------------------------

    escola = db.Column(
        db.String(200),
        nullable=False
    )

    # --------------------------------------------------------
    # NOVO RELACIONAMENTO COM ESCOLA
    # --------------------------------------------------------

    escola_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "escolas.id",
            ondelete="RESTRICT"
        ),
        nullable=True
    )

    # --------------------------------------------------------
    # CAMPO ANTIGO DE RESPONSÁVEL
    # Mantido temporariamente para compatibilidade.
    # --------------------------------------------------------

    usuario_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ========================================================
    # RELACIONAMENTOS
    # ========================================================

    # Escola da turma
    escola_relacao = db.relationship(
        "Escola",
        back_populates="turmas",
        foreign_keys=[escola_id]
    )

    # Responsável antigo da turma
    responsavel = db.relationship(
        "Usuario",
        back_populates="turmas",
        foreign_keys=[usuario_id]
    )

    # Novos vínculos entre usuários e turma
    vinculos_usuarios = db.relationship(
        "UsuarioTurma",
        back_populates="turma",
        cascade="all, delete-orphan"
    )

    # Estudantes da turma
    estudantes = db.relationship(
        "Estudante",
        back_populates="turma",
        cascade="all, delete-orphan"
    )

    # ========================================================
    # CONVERSÃO PARA JSON
    # ========================================================

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "ano": self.ano,
            "escola": self.escola,
            "escola_id": self.escola_id,
            "usuario_id": self.usuario_id,
            "data_cadastro": (
                self.data_cadastro.isoformat()
                if self.data_cadastro
                else None
            ),
            "quantidade_estudantes": len(
                self.estudantes
            )
        }


# ============================================================
# USUÁRIO ↔ TURMA
# ============================================================

class UsuarioTurma(db.Model):
    __tablename__ = "usuarios_turmas"

    # ========================================================
    # CHAVE PRIMÁRIA COMPOSTA
    # ========================================================

    usuario_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id",
            ondelete="CASCADE"
        ),
        primary_key=True,
        nullable=False
    )

    turma_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "turmas.id",
            ondelete="CASCADE"
        ),
        primary_key=True,
        nullable=False
    )

    data_vinculo = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ========================================================
    # RELACIONAMENTOS
    # ========================================================

    usuario = db.relationship(
        "Usuario",
        back_populates="vinculos_turmas"
    )

    turma = db.relationship(
        "Turma",
        back_populates="vinculos_usuarios"
    )

    # ========================================================
    # CONVERSÃO PARA JSON
    # ========================================================

    def to_dict(self):
        return {
            "usuario_id": self.usuario_id,
            "turma_id": self.turma_id,
            "data_vinculo": (
                self.data_vinculo.isoformat()
                if self.data_vinculo
                else None
            )
        }


# ============================================================
# ESTUDANTE
# ============================================================

class Estudante(db.Model):
    __tablename__ = "estudantes"

    id = db.Column(
        db.BigInteger,
        primary_key=True
    )

    nome = db.Column(
        db.String(150),
        nullable=False
    )

    matricula = db.Column(
        db.String(50),
        nullable=True
    )

    turma_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "turmas.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ========================================================
    # RELACIONAMENTOS
    # ========================================================

    turma = db.relationship(
        "Turma",
        back_populates="estudantes"
    )

    registros_saude_mental = db.relationship(
        "RegistroSaudeMental",
        back_populates="estudante",
        cascade="all, delete-orphan",
        order_by=(
            "RegistroSaudeMental.data_registro.desc()"
        )
    )

    # ========================================================
    # CONVERSÃO PARA JSON
    # ========================================================

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "matricula": self.matricula,
            "turma_id": self.turma_id,
            "data_cadastro": (
                self.data_cadastro.isoformat()
                if self.data_cadastro
                else None
            ),
            "quantidade_registros": len(
                self.registros_saude_mental
            )
        }


# ============================================================
# REGISTRO DE SAÚDE MENTAL
# ============================================================

class RegistroSaudeMental(db.Model):
    __tablename__ = "registros_saude_mental"

    id = db.Column(
        db.BigInteger,
        primary_key=True
    )

    estudante_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "estudantes.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    usuario_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "usuarios.id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    tipo = db.Column(
        db.String(100),
        nullable=False
    )

    gravidade = db.Column(
        db.String(30),
        nullable=True
    )

    descricao = db.Column(
        db.Text,
        nullable=True
    )

    data_registro = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ========================================================
    # RELACIONAMENTOS
    # ========================================================

    estudante = db.relationship(
        "Estudante",
        back_populates="registros_saude_mental"
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="registros_saude_mental"
    )

    # ========================================================
    # CONVERSÃO PARA JSON
    # ========================================================

    def to_dict(self):
        return {
            "id": self.id,
            "estudante_id": self.estudante_id,
            "usuario_id": self.usuario_id,
            "tipo": self.tipo,
            "gravidade": self.gravidade,
            "descricao": self.descricao,
            "data_registro": (
                self.data_registro.isoformat()
                if self.data_registro
                else None
            )
        }
