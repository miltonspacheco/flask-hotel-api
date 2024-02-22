from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from flask_jwt_extended import jwt_required
import sqlite3

# Normalizando dados
def normalize_path_params(cidade=None, 
                          estrelas_min=0,
                          estrelas_max=5,
                          diaria_min=0,
                          diaria_max=10000,
                          limit=50,
                          offset=0, **dados):
    if cidade:
        return{
            'estrelas_min': estrelas_min,
            'estrelas_max': estrelas_max,
            'diaria_min': diaria_min,
            'diaria_max': diaria_max,
            'cidade': cidade,
            'limit': limit,
            'offset': offset
        }
    return {
        'estrelas_min': estrelas_min,
        'estrelas_max': estrelas_max,
        'diaria_min': diaria_min,
        'diaria_max': diaria_max,
        'limit': limit,
        'offset': offset
    }

# Parâmetros para busca com filtros
path_params = reqparse.RequestParser()
path_params.add_argument('cidade', type=str)
path_params.add_argument('estrelas_min', type=float)
path_params.add_argument('estrelas_max', type=float)
path_params.add_argument('diaria_min', type=float)
path_params.add_argument('diaria_max', type=float)
path_params.add_argument('limit', type=float)
path_params.add_argument('offset', type=float)

class Hoteis (Resource):
    def get(self):
        connection = sqlite3.connect('banco.db')
        cursor = connection.cursor()
        
        dados = path_params.parse_args()      
        # Selecionando dados validor (que não são None)
        dados_validos = {chave:dados[chave] for chave in dados if dados[chave] is not None}
        parametros = normalize_path_params(**dados_validos)
        
        if not parametros.get('cidade'):
            consulta = "SELECT * FROM hoteis WHERE (estrelas >= ? and estrelas <= ?) and (diaria >= ? and diaria <= ?) LIMIT ? OFFSET ?"
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta, tupla)
        else:
            consulta = "SELECT * FROM hoteis WHERE (estrelas >= ? and estrelas <= ?) and (diaria >= ? and diaria <= ?) and cidade = ? LIMIT ? OFFSET ?"
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta, tupla)

        hoteis = []
        for linha in resultado:
            hoteis.append({
            'hotel_id': linha[0],
            'nome': linha[1],
            'estrelas': linha[2],
            'diaria': linha[3],
            'cidade': linha[4]
            })
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