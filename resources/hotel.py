from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from models.site import SiteModel
from resources.filtros import normalize_path_params, consulta_sem_cidade, consulta_com_cidade
from flask_jwt_extended import jwt_required
from settings import *
import psycopg2


# Parâmetros para busca com filtros
path_params = reqparse.RequestParser()
path_params.add_argument('cidade', type=str, location="args")
path_params.add_argument('estrelas_min', type=float, location="args")
path_params.add_argument('estrelas_max', type=float, location="args")
path_params.add_argument('diaria_min', type=float, location="args")
path_params.add_argument('diaria_max', type=float, location="args")
path_params.add_argument('limit', type=float, location="args")
path_params.add_argument('offset', type=float, location="args")

class Hoteis (Resource):
    def get(self):
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME)
        cursor = connection.cursor()
        
        dados = path_params.parse_args()      
        dados_validos = {chave:dados[chave] for chave in dados if dados[chave] is not None}
        parametros = normalize_path_params(**dados_validos)
        
        if not parametros.get('cidade'):
            tupla = tuple([parametros[chave] for chave in parametros])
            cursor.execute(consulta_sem_cidade, tupla)
            resultado = cursor.fetchall()
        else:
            tupla = tuple([parametros[chave] for chave in parametros])
            cursor.execute(consulta_com_cidade, tupla)
            resultado = cursor.fetchall()

        hoteis = []
        if resultado:
            for linha in resultado:
                hoteis.append({
                'hotel_id': linha[0],
                'nome': linha[1],
                'estrelas': linha[2],
                'diaria': linha[3],
                'cidade': linha[4],
                'site_id': linha[5]
                })

        connection.close()
        return {'hoteis': hoteis} 
    
class Hotel(Resource):
    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return {'message': 'Hotel not found.'}, 404 #not found
    
    @jwt_required()
    def post(self, hotel_id):
        # Verifica se o hotel já existe 
        if HotelModel.find_hotel(hotel_id):
            return {"message": "Hotel id '{}' already existis.".format(hotel_id)}, 400
        # Valida a solicitação com base nos argumentos
        dados = Hotel.argumentos.parse_args()
        # Cria o hotel
        hotel = HotelModel(hotel_id, **dados)

        if not SiteModel.find_site_by_id(dados.get('site_id')):
            return{'message': 'The hotel must be associated to a valid site id.'}, 400
        try:
            hotel.save_hotel()
        except:
            return {'message': 'Error trying to save hotel.'}, 500 #internal error
        return hotel.json()

    @jwt_required()
    def put(self, hotel_id):
        # Valida a solicitação com base nos argumentos
        dados = Hotel.argumentos.parse_args()
        # Busca o hotel
        hotel_found = HotelModel.find_hotel(hotel_id)

        if hotel_found:
            hotel_found.update_hotel(**dados)
            hotel_found.save_hotel()
            return hotel_found.json(), 200
        # Se não for encontrado, é criado
        hotel = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel()
        except:
            return {'message': 'Error trying to save hotel.'}, 500 #internal error
        return hotel.json(), 201 #created
    
    @jwt_required()
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
            except:
                return {'message': 'Error trying to delete hotel.'}, 500 #internal error
            return {'message': 'Hotel deleted.'}
        return {'message': 'Hotel not found.'}, 404


    # Define os argumentos
    argumentos = reqparse.RequestParser()
    argumentos.add_argument('nome', type=str, required=True, help="The field 'nome' cannot be left blank.")# Nao pode estar vazio (argumentos obrigatorios)
    argumentos.add_argument('estrelas', type=float, required=True, help="The field 'estrelas' cannot be left blank.")# Nao pode estar vazio (argumentos obrigatorios)
    argumentos.add_argument('diaria')
    argumentos.add_argument('cidade')
    argumentos.add_argument('site_id', type=int, required=True, help='Every hotel needs to be linked with a site')