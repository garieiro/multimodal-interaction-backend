import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from statistics import *
import re
import os


import inflect

app = Flask(__name__)
CORS(app)

selected_file = "data.json"

# Função para ler o JSON
def read_json_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found")

    with open(file_path, 'r') as file:
        return json.load(file)

# Handler para erro 404 (Not Found)
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

# Handler para erro 500 (Internal Server Error)
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"error": "An internal server error occurred. Please try again later."}), 500

##### MELHORAR ISTO #####

# Endpoint para listar os ficheiros disponíveis
@app.route('/files', methods=['GET'])
def list_files():
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    return jsonify(files)

# Endpoint para selecionar o ficheiro
@app.route('/select-file', methods=['GET'])
def select_file():
    file_name = request.args.get('file_name')
    if file_name:
        file_path = os.path.join('.', file_name)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as file:
                content = file.read().strip()
                if content:
                    return jsonify({
                        'status': 'success', 
                        'message': f'File set to {file_name}', 
                        'content': content
                    })
                else:
                    return jsonify({'status': 'error', 'message': 'File is empty'}), 400
        else:
            return jsonify({'status': 'error', 'message': 'File does not exist or is empty'}), 400
    return jsonify({'status': 'error', 'message': 'No file provided'}), 400

##### FIM #####

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

#Stacked Bar Chart
#Retorna o número de Types dentro de cada experiência
@app.route('/events/count/types', methods=['GET'])
def count_types():
    
    supported_filters = []

    query_params = request.args

    for param in query_params:
        if param not in supported_filters:
            return jsonify({"error": 'Filter "{}" not supported'.format(param)}), 400

    json_content = read_json_file(selected_file)
    result = []

    for idx, experience in enumerate(json_content):
        type_counts = {}
        for event in experience:
            event_type = event.get('Type')
            if event_type:
                if event_type in type_counts:
                    type_counts[event_type] += 1
                else:
                    type_counts[event_type] = 1
        
        for event_type, count in type_counts.items():
            result.append({
                "name": f"{idx + 1}",
                "type": event_type,
                "count": count
            })

    return jsonify(result)

#Retorna o número total de eventos Type ou EventType
@app.route('/events/count', methods=['GET'])
def count_events():
    json_content = read_json_file(selected_file)
    type_param = request.args.get('type')
    event_type_param = request.args.get('eventType')

    if type_param is None and event_type_param is None:
        return jsonify({'error': 'At least one of the query parameters "type" or "eventType" must be provided'}), 400

    event_counts = {}

    for event_list in json_content:
        for event in event_list:
            if type_param and event.get('Type') == type_param:
                event_type = event.get('Type')
            elif event_type_param and event.get('EventType') == event_type_param:
                event_type = event.get('EventType')
            else:
                continue

            if event_type:
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

    print(event_counts)
    return jsonify(event_counts)

#Retorna informação total para o Sunburst
@app.route('/events/exps', methods=['GET'])
def get_all_exps():
    json_content = read_json_file(selected_file)
    total_exps = len(json_content)
    p = inflect.engine()
    exps_data = {
        "name": "exp",
        "children": [{"name": f"{p.ordinal(i + 1)} exp", "children": []} for i in range(total_exps)]
    }
    
    for i, exp_events in enumerate(json_content):
        added_types = set()  
        type_event_map = {}  
        
        for event in exp_events:
            event_type = event.get('Type')
            event_eventType = event.get('EventType')
            duration = calculate_duration(event.get('Start'), event.get('End'))
            
           
            if event_type and event_type not in added_types:
                added_types.add(event_type)  
                type_event_map[event_type] = {"name": event_type, "children": []}
                
            if event_eventType not in type_event_map[event_type]["children"]:
                type_event_map[event_type]["children"].append({"name": event_eventType, "value": duration})

        exps_data["children"][i]["children"].extend(type_event_map.values())

    return jsonify(exps_data)

#Retorna a contagem das palavras encontradas na totalidade, em cada experiência ou então por type
@app.route('/events/words', methods=['GET'])
def extract_words():
    json_content = read_json_file(selected_file)
    exp_param = request.args.get('exp')  # Obter o parâmetro 'exp' da consulta
    type_param = request.args.get('type')  # Obter o parâmetro 'type' da consulta

    if exp_param is not None:
        try:
            exp_index = int(exp_param)  # Converta o parâmetro 'exp' para um índice de lista
            exp_words = []

            if exp_index >= 0 and exp_index < len(json_content):
                for entry in json_content[exp_index]:
                    semantic_result = entry.get('Semantic', {}).get('RESULT', '')
                    entry_type = entry.get('Type', '')

                    if type_param:
                        if entry_type.lower() == type_param.lower():
                            for word in re.findall(r'\b\w+\b', semantic_result):
                                word_object = next((item for item in exp_words if item["text"] == word), None)
                                if word_object:
                                    word_object["value"] += 1
                                else:
                                    exp_words.append({"text": word, "value": 1})
                    else:
                        for word in re.findall(r'\b\w+\b', semantic_result):
                            word_object = next((item for item in exp_words if item["text"] == word), None)
                            if word_object:
                                word_object["value"] += 1
                            else:
                                exp_words.append({"text": word, "value": 1})
                
                return jsonify(exp_words)
            else:
                return jsonify({"error": f"Experience {exp_param} not found"}), 404
        except ValueError:
            return jsonify({"error": "Invalid value for 'exp' parameter"}), 400

    else:  # Se nenhum parâmetro 'exp' for fornecido, retornar todas as palavras de todas as experiências
        words = []

        for entry_list in json_content:
            for entry in entry_list:
                semantic_result = entry.get('Semantic', {}).get('RESULT', '')
                entry_type = entry.get('EventType', '')

                if type_param:
                    if entry_type.lower() == type_param.lower():
                        for word in re.findall(r'\b\w+\b', semantic_result):
                            word_object = next((item for item in words if item["text"] == word), None)
                            if word_object:
                                word_object["value"] += 1
                            else:
                                words.append({"text": word, "value": 1})
                else:
                    for word in re.findall(r'\b\w+\b', semantic_result):
                        word_object = next((item for item in words if item["text"] == word), None)
                        if word_object:
                            word_object["value"] += 1
                        else:
                            words.append({"text": word, "value": 1})

        return jsonify(words)



#Other funcions
def calculate_duration(start_time, end_time):
    format = "%Y-%m-%d %H:%M:%S.%f"
    start = datetime.strptime(start_time, format)
    end = datetime.strptime(end_time, format)
    duration = end - start
    
    return duration.total_seconds()




#Não estou a usar!!!
@app.route('/events/total', methods=['GET'])
def get_total_events():
    json_content = read_json_file(selected_file)
    total_events = len(json_content)
    error_experiences = 0
    successful_experiences = 0
    
    for experience in json_content:
        has_error = False
        for event in experience:
            if 'Type' in event and event['Type'] == 'ERROR':
                has_error = True
                break 
        if has_error:
            error_experiences += 1
        else:
            successful_experiences += 1
    
    return jsonify({
        "total_experiences": total_events,
        "error_experiences": error_experiences,
        "successful_experiences": successful_experiences
    })








@app.route('/events/expDurations', methods=['GET'])
def get_exp_durations():
    json_content = read_json_file(selected_file)
    exp_param = request.args.get('exp')
    
    if exp_param is not None:
        exp_index = int(exp_param)
        if exp_index < 0 or exp_index >= len(json_content):
            return jsonify({"error": "Invalid exp index"}), 400
        
        exp_events = json_content[exp_index]
        event_durations_by_type = {}
        
        for event in exp_events:
            event_type = event.get('Type')
            event_duration = calculate_duration(event.get('Start'), event.get('End'))
            
            # Calcula a duração para cada tipo de evento
            if event_type in event_durations_by_type:
                event_durations_by_type[event_type].append(event_duration)
            else:
                event_durations_by_type[event_type] = [event_duration]
        
        result = [{"label": event_type, "values": durations} for event_type, durations in event_durations_by_type.items()]
        
        return jsonify(result)
    
    else:
        exp_durations_by_type = {}
        
        for exp_events in json_content:
            for event in exp_events:
                event_type = event.get('Type')
                event_duration = calculate_duration(event.get('Start'), event.get('End'))
                
                if event_type in exp_durations_by_type:
                    exp_durations_by_type[event_type].append(event_duration)
                else:
                    exp_durations_by_type[event_type] = [event_duration]
        
        # Transforma os dados em um formato de lista de objetos com rótulo e valores
        result = [{"label": event_type, "values": durations} for event_type, durations in exp_durations_by_type.items()]
        
        return jsonify(result)



# Retorna o nº de experiências existentes
@app.route('/events/expCount', methods=['GET'])
def get_exp_count():
    json_content = read_json_file(selected_file)
    num_experiences = {}
    if not json_content:
        return jsonify([])

    else:
        total_experiences = len(json_content)
        
        return jsonify({"total": total_experiences})

# Retorna os dados para o meu gráfico Sankey
@app.route('/events/sankey', methods=['GET'])
def generate_sankey_data():
    json_content = read_json_file(selected_file)
    exp_param = request.args.get('exp')  # Obter o parâmetro 'exp' da consulta

    if exp_param is not None:
        try:
            exp_index = int(exp_param)  # Converta o parâmetro 'exp' para um índice de lista

            if exp_index >= 0 and exp_index < len(json_content):
                experience = json_content[exp_index]

                # Extração de nós e criação de índice
                nodes_set = set()
                for entry in experience:
                    nodes_set.add(entry['Source'])
                    nodes_set.add(entry['Target'])

                nodes = list(nodes_set)
                nodes_index = {name: index for index, name in enumerate(nodes)}

                # Formatação correta de nós e links
                formatted_nodes = [{"name": name, "category": next((entry['Type'] for entry in experience if entry['Source'] == name or entry['Target'] == name), "default")} for name in nodes]
                formatted_links = []
                for entry in experience:
                    source_index = entry['Source']
                    target_index = entry['Target']
                    duration = calculate_duration(entry.get('Start'), entry.get('End'))
                    formatted_links.append({"source": source_index, "target": target_index, "value": duration})

                return jsonify({"nodes": formatted_nodes, "links": formatted_links})
            else:
                return jsonify({"error": f"Experience {exp_param} not found"}), 404
        except ValueError:
            return jsonify({"error": "Invalid value for 'exp' parameter"}), 400

    else:  # Se nenhum parâmetro 'exp' for fornecido, retornar todos os dados necessários para o gráfico de Sankey
        nodes_set = set()
        for experience in json_content:
            for entry in experience:
                nodes_set.add(entry['Source'])
                nodes_set.add(entry['Target'])

        nodes = list(nodes_set)
        nodes_index = {name: index for index, name in enumerate(nodes)}

        formatted_nodes = [{"name": name, "category": next((entry['Type'] for entry in experience if entry['Source'] == name or entry['Target'] == name), "default")} for name in nodes]
        formatted_links = []
        for experience in json_content:
            for entry in experience:
                source_index = nodes_index[entry['Source']]
                target_index = nodes_index[entry['Target']]
                duration = calculate_duration(entry['Start'], entry['End'])
                formatted_links.append({"source": source_index, "target": target_index, "value": duration})

        return jsonify({"nodes": formatted_nodes, "links": formatted_links})



@app.route('/events/times', methods=['GET'])
def get_all_times():
    json_content = read_json_file(selected_file)
    # Obter o parâmetro de consulta 'exp_id', se fornecido
    exp_id = request.args.get('exp_id', type=int)
    p = inflect.engine()
    if exp_id is not None:
        if exp_id < 1 or exp_id > len(json_content):
            return jsonify({"error": "Experience ID out of range"}), 400

        event_list = json_content[exp_id - 1]
        event_data = extract_event_data(event_list)
        return jsonify(event_data)

    # Se nenhum parâmetro for fornecido, retornar todas as experiências
    formatted_data = []
    for idx, event_list in enumerate(json_content):
        label = f"{p.ordinal(idx + 1)} exp"
        times = extract_event_times(event_list)
        event_data = {"label": label, "times": times}
        formatted_data.append(event_data)

    return jsonify(formatted_data)


def extract_event_data(event_list):
    event_data = []
    event_types = set(event['EventType'] for event in event_list)

    for event_type in event_types:
        for event in event_list:  # Corrigindo aqui
            if event['EventType'] == event_type:
                times = extract_event_times(event_list, event_type)
                event_data.append({"type": event['Type'], "label": event_type, "times": times})

    return event_data


def extract_event_times(event_list, event_type=None):
    times = []

    for event in event_list:
        if event_type is None or event['EventType'] == event_type:
            starting_time = convert_to_milliseconds(event['Start'])
            ending_time = convert_to_milliseconds(event['End'])
            times.append({"starting_time": starting_time, "ending_time": ending_time})

    return times


def convert_to_milliseconds(time_string):
    datetime_obj = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S.%f")
    milliseconds = int(datetime_obj.timestamp() * 1000)
    return milliseconds


@app.route('/events/pie-chart', methods=['GET'])
def get_pie_chart_data():
    json_content = read_json_file(selected_file)
    data = {'children': []}

    # Dicionário para contar ocorrências de type, eventType e Source
    type_eventType_source_count = {}

    # Loop para contar ocorrências de type, eventType e Source
    for event_list in json_content:
        for event in event_list:
            if event.get('Type') == 'OUTPUT':
                event_type = event.get('Type')
                event_eventType = event.get('EventType')
                event_source = event.get('Source')

                # Incrementar contagem
                key = (event_type, event_eventType, event_source)
                type_eventType_source_count[key] = type_eventType_source_count.get(key, 0) + 1

    # Loop para criar a estrutura de dados desejada
    for key, count in type_eventType_source_count.items():
        event_type, event_eventType, event_source = key

        # Dicionário para contar ocorrências de semantic.result
        semantic_result_count = {}

        # Loop para contar ocorrências de semantic.result
        for event_list in json_content:
            for event in event_list:
                if (event.get('Type'), event.get('EventType'), event.get('Source')) == key:
                    semantic_result = event.get('Semantic', {}).get('RESULT', 'Unknown')
                    semantic_result_count[semantic_result] = semantic_result_count.get(semantic_result, 0) + 1

        # Lista de dicionários para o segundo nível
        children = [{'name': semantic_result, 'value': count} for semantic_result, count in semantic_result_count.items()]

        # Adicionar dados ao primeiro nível
        data['children'].append({'type': event_type, 'name': event_eventType, 'children': children})

    return jsonify(data)


@app.route('/events/type-semantic', methods=['GET'])
def get_type_semantic_data():
    json_content = read_json_file(selected_file)
    data = {'children': []}

    # Dicionário para contar ocorrências de Type e Semantic
    type_semantic_count = {}

    # Loop para contar ocorrências de Type e Semantic
    for event_list in json_content:
        for event in event_list:
            if event.get('Type') == 'ERROR':
                event_type = event.get('Type')
                semantic_result = event.get('Semantic', {}).get('RESULT', 'Unknown')

                # Incrementar contagem
                key = (event_type, semantic_result)
                type_semantic_count[key] = type_semantic_count.get(key, 0) + 1

    # Loop para criar a estrutura de dados desejada
    for key, count in type_semantic_count.items():
        event_type, semantic_result = key

        # Adicionar dados ao primeiro nível
        data['children'].append({'type': event_type, 'semantic': semantic_result, 'value': count})

    return jsonify(data)



















@app.route('/events/filter', methods=['GET'])
def filter_events():

    type_param = request.args.get('type')  
    eventType_param = request.args.get('eventType')  
    exp_param = request.args.get('exp')
    filtered_data = []

    # Verifica se pelo menos um dos parâmetros está presente
    if type_param is None and eventType_param is None and exp_param is None:
        return jsonify({'error': 'At least one of the query parameters "type", "eventType", or "exp" must be provided'}), 400

    # Se o parâmetro exp estiver presente, verifica se é um número válido
    if exp_param is not None:
        try:
            exp_index = int(exp_param)
            if exp_index < 0 or exp_index >= len(json_content):
                return jsonify({'error': f'exp index {exp_index} is out of range'}), 400
        except ValueError:
            return jsonify({'error': 'exp parameter must be an integer'}), 400

        for event in json_content[exp_index]:
            if (type_param is None or event.get('Type') == type_param) and \
                (eventType_param is None or event.get('EventType') == eventType_param):
                filtered_data.append(event)

    else:
        for event_list in json_content:
            for event in event_list:
                if (type_param is None or event.get('Type') == type_param) and \
                   (eventType_param is None or event.get('EventType') == eventType_param):
                    filtered_data.append(event)

    if filtered_data:
        return jsonify(filtered_data)
    else:
        return jsonify({'error': 'No events found for the specified criteria'}), 404


if __name__ == '__main__':
    app.run(debug=True)
