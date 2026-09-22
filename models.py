
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ============================================================
# USUÁRIO
# ============================================================

class Usuario(db.Model):
    __tablename__ = "usuarios"
    __table_args__ = {"extend_existing": True}

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

    escola = db.Column(
        db.String(200)
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

    turmas = db.relationship(
        "Turma",
        back_populates="responsavel",
        foreign_keys="Turma.usuario_id"
    )

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

    escola = db.Column(
        db.String(200),
        nullable=False
    )

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

    responsavel = db.relationship(
        "Usuario",
        back_populates="turmas",
        foreign_keys=[usuario_id]
    )

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
        order_by="RegistroSaudeMental.data_registro.desc()"
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
```
