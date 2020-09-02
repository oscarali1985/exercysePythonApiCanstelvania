"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, Donante, Perfil, Muestra, Visita
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# endpoints recurso donantes
@app.route("/donantes", methods=["GET", "POST"])
def cr_donantes():
    """
        "GET": devolver lista de todos los donantes
        "POST": crear un donante y devolver su información
    """
    # averiguar si es GET o POST
    if request.method == "GET":
        #   seleccionar todos los registros de la tabla donantes - usando flask-sqlalchemy
        #   crear una variable lista y asignarle todos los donantes que devuelva la consulta
        donantes = Donante.query.all()
        # verificamos si hay parámetros en la url y filtramos la lista con eso
        name = request.args.get("name")
        if name is not None:
            donantes_filtrados = filter(lambda donante: name.lower() in donante.nombre_completo.lower(), donantes)
        else:
            donantes_filtrados = donantes
        #   serializar los objetos de la lista - tendría una lista de diccionarios
        donantes_serializados = list(map(lambda donante: donante.serializar(), donantes_filtrados))
        print(donantes_serializados)
        #   devolver la lista jsonificada y 200_OK
        return jsonify(donantes_serializados), 200
    else:
        #   crear una variable y asignarle diccionario con datos para crear donante
        insumos_donante = request.json # request.get_json()
        if insumos_donante is None:
            return jsonify({
                "resultado": "no envió insumos para crear el donante..."
            }), 400
        #   verificar que el diccionario tenga cedula, nombre, apellido
        if (
            "cedula" not in insumos_donante or
            "nombre" not in insumos_donante or
            "apellido" not in insumos_donante
        ):
            return jsonify({
                "resultado": "revise las propiedades de su solicitud"
            }), 400
        #   validar que campos no vengan vacíos y que cédula tenga menos de 14 caracteres
        if (
            insumos_donante["nombre"] == "" or
            insumos_donante["apellido"] == "" or
            insumos_donante["cedula"] == "" or
            len(str(insumos_donante["cedula"])) > 14
        ):
            return jsonify({
                "resultado": "revise los valores de su solicitud"
            }), 400
        #   crear una variable y asignarle el nuevo donante con los datos validados
        nuevo_donante = Donante.registrarse(
            insumos_donante["cedula"],
            insumos_donante["nombre"],
            insumos_donante["apellido"]
        )
        #   agregar a la sesión de base de datos (sqlalchemy) y hacer commit de la transacción
        db.session.add(nuevo_donante)
        try:
            db.session.commit()
            # devolvemos el nuevo donante serializado y 201_CREATED
            return jsonify(nuevo_donante.serializar()), 201
        except Exception as error:
            db.session.rollback()
            print(f"{error.args} {type(error)}")
            # devolvemos "mira, tuvimos este error..."
            return jsonify({
                "resultado": f"{error.args}"
            }), 500

@app.route("/donantes/<donante_id>", methods=["GET", "PATCH", "DELETE"])
def crud_donantes(donante_id):
    """
        GET: devolver el detalle de un donante específico
        PATCH: actualizar datos del donante específico,
            guardar en base de datos y devolver el detalle
        DELETE: eliminar el donante específico y devolver 204 
    """
    # crear una variable y asignar el donante específico
    donante = Donante.query.get(donante_id)
    # verificar si el donante con id donante_id existe
    if isinstance(donante, Donante):
        if request.method == "GET":
            # devolver el donante serializado y jsonificado. Y 200
            return jsonify(donante.serializar()), 200
        elif request.method == "PATCH":
            # recuperar diccionario con insumos del body del request
            diccionario = request.get_json()
            # actualizar propiedades que vengan en el diccionario
            donante.actualizar_donante(diccionario)
            # guardar en base de datos, hacer commit
            try:
                db.session.commit()
                # devolver el donante serializado y jsonificado. Y 200 
                return jsonify(donante.serializar()), 200
            except Exception as error:
                db.session.rollback()
                print(f"{error.args} {type(error)}")
                return jsonify({
                    "resultado": f"{error.args}"
                }), 500
        else:
            # remover el donante específico de la sesión de base de datos
            db.session.delete(donante)
            # hacer commit y devolver 204
            try:
                db.session.commit()
                return jsonify({}), 204
            except Exception as error:
                db.session.rollback()
                print(f"{error.args} {type(error)}")
                return jsonify({
                    "resultado": f"{error.args}"
                }), 500
    else:
        # el donante no existe!
        return jsonify({
            "resultado": "el donante no existe..."
        }), 404

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
