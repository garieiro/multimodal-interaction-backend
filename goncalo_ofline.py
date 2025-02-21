import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from collections import Counter
from statistics import *
import re
import os
import inflect

app = Flask(__name__)
CORS(app)

selected_file = "dataset1.json"

### Funções para mostrar erros ### 

# Handler para erro 404 (Not Found)
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

# Handler para erro 500 (Internal Server Error)
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "An internal server error occurred. Please try again later."}), 500

### Fim ###

### Funções auxiliares ###

# Função para contar o número de utilizadores no JSON
def count_users(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
    except Exception as e:
        print(f"Erro ao ler o arquivo {file_path}: {e}")
        return 0

# Função para calcular a duração em segundos entre dois timestamps
def calculate_duration(start_time, end_time):
    format = "%Y-%m-%d %H:%M:%S.%f"
    start = datetime.strptime(start_time, format)
    end = datetime.strptime(end_time, format)
    duration = end - start
    
    return duration.total_seconds()

# Função para calcular a duração total do user
def calculate_user_duration(events):
    try:
        start_time = events[0]['Start']
        end_time = events[-1]['End']
        return calculate_duration(start_time, end_time)
    except (KeyError, IndexError, ValueError) as e:
        print(f"Erro ao calcular duração do usuário: {str(e)}")
        return None

# Função para contar usuários e calcular tempo
def count_users_and_duration(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    users_info = []
    
    for user_data in data:
        user_duration = calculate_user_duration(user_data)
        if user_duration is not None:
            users_info.append({
                'user': f"User {len(users_info) + 1}",
                'duration': user_duration
            })
    
    return users_info

def count_types(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    types_counter = Counter()
    
    for event_list in data:
        for entry in event_list:
            type_value = entry.get('Type')
            if type_value:
                types_counter[type_value] += 1
    
    # Verifica se o Counter está vazio
    if not types_counter:
        return '0'
    
    return dict(types_counter)

def count_event_types(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    event_types_counter = Counter()
    
    for event_list in data:
        for entry in event_list:
            event_type_value = entry.get('EventType')
            if event_type_value:
                event_types_counter[event_type_value] += 1
    
    # Verifica se o Counter está vazio
    if not event_types_counter:
        return '0'
    
    return dict(event_types_counter)

# Função para ler o JSON
def read_json_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found")

    with open(file_path, 'r') as file:
        return json.load(file)

# Função para transformar o dataset
def load_dataset(file_name):
    data = read_json_file(file_name)
    # Convertendo a lista de listas em um dicionário com índices
    dataset_dict = {str(index): events for index, events in enumerate(data, start=1)}
    return dataset_dict

# Endpoint para listar os ficheiros disponíveis e o número de utilizadores
@app.route('/files', methods=['GET'])
def list_files():
    try:
        dataset_name = request.args.get('dataset') 

        files = [f for f in os.listdir('.') if f.endswith('.json')]
        files_info = []
        
        if not dataset_name:
            for file in files:
                file_path = os.path.join('.', file)
                
                users_info = count_users_and_duration(file_path)
                type_counts = count_types(file_path)
                event_type_counts = count_event_types(file_path)
                
                total_duration = sum(user['duration'] for user in users_info)
                
                files_info.append({
                    'dataset': file,
                    'users': len(users_info),
                    'total_duration': total_duration,
                    'type_counts': type_counts,
                    'event_type_counts': event_type_counts
                })
        else:
            for file in files:
                if dataset_name != file:
                    continue
                
                file_path = os.path.join('.', file)
                users_info = count_users_and_duration(file_path)
                files_info.extend(users_info)

        return jsonify(files_info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#Endpoint retorna os eventos de um dataset para um conjunto de users
@app.route('/submit', methods=['GET'])
def get_filtered_data():
    dataset_name = request.args.get('dataset')
    users = request.args.get('users')
    
    if not dataset_name or not users:
        return jsonify({"error": "Parâmetros 'dataset' e 'users' são obrigatórios"}), 400

    user_list = users.split(',')
    
    try:
        dataset = load_dataset(dataset_name)
    except FileNotFoundError:
        return jsonify({"error": "Dataset não encontrado"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Erro ao ler o dataset"}), 500

    print(f"Dataset: {dataset}")
    print(f"User List: {user_list}")
    
    filtered_data = {user: dataset.get(user) for user in user_list if user in dataset}

    return jsonify(filtered_data)
    
# NOT USE
# Retorna a totalidade de eventos
@app.route('/events', methods=['GET'])
def get_all_data():
    json_content = read_json_file(selected_file)
    return jsonify(json_content)

# Retorna todos os types existentes
@app.route('/events/types', methods=['GET'])
def get_all_types():
    json_content = read_json_file(selected_file)
    all_types = set()
    for event_list in json_content:
        for event in event_list:
            if 'Type' in event:
                all_types.add(event['Type'])

    return jsonify(list(all_types))

# Retorna todos os EventTypes existentes
@app.route('/events/eventTypes', methods=['GET'])
def get_all_eventTypes():
    json_content = read_json_file(selected_file)
    all_eventTypes = set()
    for event_list in json_content:
        for event in event_list:
            if 'EventType' in event:
                all_eventTypes.add(event['EventType'])

    return jsonify(list(all_eventTypes))

# Retorna todos as Sources existentes
@app.route('/events/sources', methods=['GET'])
def get_all_sources():
    json_content = read_json_file(selected_file)
    all_sources = set()
    for event_list in json_content:
        for event in event_list:
            if 'Source' in event:
                all_sources.add(event['Source'])

    return jsonify(list(all_sources)) 

# Retorna todos os Targets existentes
@app.route('/events/targets', methods=['GET'])
def get_all_targets():
    json_content = read_json_file(selected_file)
    all_targets = set()
    for event_list in json_content:
        for event in event_list:
            if 'Target' in event:
                all_targets.add(event['Target'])

    return jsonify(list(all_targets)) 

if __name__ == '__main__':
    app.run(debug=True)
