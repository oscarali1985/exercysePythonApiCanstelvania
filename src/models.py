from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json

db = SQLAlchemy()

# clase para donantes que visitan el banco de sangre
class Donante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(14), unique=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)

    perfil = db.relationship("Perfil", backref="donante", uselist=False)

    def __init__(self, cedula, nombre, apellido):
        """ crea y devuelve una instancia de esta clase """
        self.cedula = cedula
        self.nombre = nombre
        self.apellido = apellido

    def __str__(self):
        return f"\t{self.cedula:10} ->  {self.nombre_completo}"

    @classmethod
    def cargar(cls):
        """
            abre el archivo donante.json y carga en la 
            variable donantes objetos donante para cada
            uno de los diccionarios de la lista
        """
        _donantes = []
        try:
            with open("./donante.json", "r") as donante_archivo:
                donantes_diccionarios = json.load(donante_archivo)
                for donante in donantes_diccionarios:
                    nuevo_donante = cls.registrarse(
                        donante["cedula"],
                        donante["nombre"],
                        donante["apellido"]
                    )
                    _donantes.append(nuevo_donante)
        except:
            with open("./donante.json", "w") as donante_archivo:
                pass
        return _donantes

    @staticmethod
    def salvar(donantes):
        """
            guarda donantes en formato json en el archivo
            correspondiente
        """
        with open("./donante.json", "w") as donante_archivo:
            donantes_serializados = []
            for donante in donantes:
                donantes_serializados.append(donante.serializar())
            json.dump(donantes_serializados, donante_archivo)

    @classmethod
    def registrarse(cls, cedula, nombre, apellido):
        """
            normaliza insumos nombre y apellido,
            crea un objeto de la clase Donante con
            esos insumos y devuelve la instancia creada.
        """
        nuevo_donante = cls(
            cedula,
            nombre.lower().capitalize(),
            apellido.lower().capitalize()
        )
        return nuevo_donante

    @property
    def nombre_completo(self):
        """ devuelve nombre + ' ' apellido """
        return f"{self.nombre} {self.apellido}"

    def serializar(self):
        """ devuelve un diccionario con data del objeto """
        return {
            "cedula": self.cedula,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "nombre_completo": self.nombre_completo
        }

# clase para el perfil de un donante
class Perfil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hepatitis = db.Column(db.Boolean(), default=False)
    VIH = db.Column(db.Boolean(), default=False)
    telefono = db.Column(db.String(15))
    fecha_nacimiento = db.Column(db.DateTime(timezone=True))
    email = db.Column(db.String(100))
    RH_positivo = db.Column(db.Boolean())
    sangre_tipo = db.Column(db.String(2))

    donante_id = db.Column(db.Integer, db.ForeignKey("donante.id"), nullable=False)

    def __init__(self, donante_id):
        self.donante_id = donante_id

    @classmethod
    def crear(cls, donante_cedula):
        """ crea y devuelve una instancia de Perfil de donante """
        return cls(donante_cedula)
        
    def actualizar_perfil(self, diccionario):
        """ actualiza propiedades del perfil según el contenido del diccionario """
        for (key, value) in diccionario.items():
            if hasattr(self, key):
                self[key] = value
        return True

# clase para una visita de un donante
class Visita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_hora = db.Column(db.DateTime(timezone=True), nullable=False)
    encuestador = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(30))
    orientacion_sexual = db.Column(db.String(30))
    ultimo_consumo_psicotropicas = db.Column(db.DateTime(timezone=True))
    ultimo_periodo_menstrual = db.Column(db.DateTime(timezone=True))
    ultimo_tatuaje = db.Column(db.DateTime(timezone=True))

    donante_id = db.Column(db.Integer, db.ForeignKey("donante.id"), nullable=False)

    def __init__(self, donante_id, encuestador): 
        self.fecha_hora = datetime.now(timezone.utc)
        self.donante_id = donante_id
        self.encuestador = encuestador
        
    @classmethod
    def crear(cls, donante_cedula, fecha_hora):
        """ crea y devuelve una instancia de visita """
        return cls(donante_cedula, fecha_hora)

    def actualizar(self, diccionario):
        """
            verificar y actualizar el valor de las propiedades
            del diccionario que correspondan al objeto visita
        """
        for (key, value) in diccionario.items():
            if hasattr(self, key):
                self[key] = value
        return True
    
    def calcular_resultado(self, diccionario_respuestas):
        """
            implementa reglas de negocio para determinar y devolver verdadero
            si un donante es apto para donar sangre en esta visita, falso caso contrario
        """
        pass

# clase para una Muestra de la sangre donada por un Donante en una Visita
class Muestra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_hora = db.Column(db.DateTime(timezone=True))
    tiene_enfermedad = db.Column(db.Boolean(), default=False)
    bioanalista = db.Column(db.String(30))

    visita_id = db.Column(db.Integer, db.ForeignKey("visita.id"), nullable=False)

    def __init__(self, visita_id):
        self.visita_id = visita_id

    @classmethod    
    def crear(cls, visita_fecha_hora, donante_cedula):
        """ crea y devuelve una instancia de la clase Muestra """
        return cls(visita_fecha_hora, donante_cedula)

    def registrar_resultado(self, fecha_hora, tiene_enfermedad, bioanalista):
        """ actualiza las propiedades del objeto muestra con base en los parámetros recibidos """
        self.fecha_hora = fecha_hora
        self.tiene_enfermedad = tiene_enfermedad
        self.bioanalista = bioanalista
        return True