import time
import json
import os
from flask import Flask, render_template, request, jsonify
from gpiozero import OutputDevice

app = Flask(__name__)

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = '/home/admin/bardrink'
PATH_STATS = os.path.join(BASE_DIR, 'estatisticas.json')

# --- CONFIGURAÇÃO DO HARDWARE (GPIO) ---
bombas = {
    "bomba1": OutputDevice(17, active_high=False, initial_value=False),
    "bomba2": OutputDevice(27, active_high=False, initial_value=False),
    "bomba3": OutputDevice(22, active_high=False, initial_value=False),
    "bomba4": OutputDevice(10, active_high=False, initial_value=False),
    "bomba5": OutputDevice(9,  active_high=False, initial_value=False),
    "bomba6": OutputDevice(11, active_high=False, initial_value=False)
}

SEC_PER_ML = 0.2 # Calibração (segundos por ml)

# --- RECEITAS ---
RECEITAS = {
    "gin_tonica": {"bomba1": 50, "bomba2": 150},
    "vodka_juice": {"bomba3": 50, "bomba4": 150},
    "sex_on_beach": {"bomba3": 40, "bomba4": 100, "bomba5": 40},
    "mojito": {"bomba6": 50, "bomba2": 150, "bomba5": 20},
    "pina_colada": {"bomba3": 50, "bomba4": 100, "bomba6": 50},
    "especial": {"bomba1": 30, "bomba5": 100, "bomba6": 20},
    "dose_gin": {"bomba1": 50},
    "dose_vodka": {"bomba3": 50},
    "dose_suco": {"bomba4": 150}
}

# --- FUNÇÕES DE ESTATÍSTICAS ---
def carregar_stats():
    if not os.path.exists(PATH_STATS):
        # Cria o arquivo inicial se não existir
        stats = {k: 0 for k in RECEITAS.keys()}
        salvar_stats(stats)
        return stats
    try:
        with open(PATH_STATS, 'r') as f:
            return json.load(f)
    except:
        return {k: 0 for k in RECEITAS.keys()}

def salvar_stats(stats):
    with open(PATH_STATS, 'w') as f:
        json.dump(stats, f)

# --- ROTAS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preparar', methods=['POST'])
def preparar():
    data = request.get_json()
    id_bebida = data.get('id')
    receita = RECEITAS.get(id_bebida)
    
    if not receita:
        return jsonify({"status": "Erro", "msg": "Receita não encontrada"}), 404

    try:
        # Execução sequencial das bombas
        for bomba_id, ml in receita.items():
            bomba = bombas.get(bomba_id)
            if bomba:
                tempo = ml * SEC_PER_ML
                bomba.on()
                time.sleep(tempo)
                bomba.off()
                time.sleep(0.5) # Pausa técnica entre ingredientes

        # Atualiza estatísticas após o preparo bem-sucedido
        stats = carregar_stats()
        stats[id_bebida] = stats.get(id_bebida, 0) + 1
        salvar_stats(stats)

        nome_exibicao = id_bebida.replace('_', ' ').title()
        return jsonify({"status": "Sucesso", "msg": f"{nome_exibicao} finalizado!"})
    
    except Exception as e:
        return jsonify({"status": "Erro", "msg": str(e)}), 500

@app.route('/get_stats')
def get_stats():
    return jsonify(carregar_stats())

@app.route('/zerar_stats', methods=['POST'])
def zerar_stats():
    stats = {k: 0 for k in RECEITAS.keys()}
    salvar_stats(stats)
    return jsonify({"status": "Sucesso"})

@app.route('/testar_bomba', methods=['POST'])
def testar_bomba():
    data = request.get_json()
    b_id = data.get('bomba')
    acao = data.get('acao') # 'on' ou 'off'
    
    bomba = bombas.get(b_id)
    if bomba:
        if acao == 'on':
            bomba.on()
        else:
            bomba.off()
        return jsonify({"status": "OK"})
    return jsonify({"status": "Erro"}), 400

@app.route('/limpar', methods=['POST'])
def limpar():
    try:
        for b in bombas.values(): b.on()
        time.sleep(15)
        for b in bombas.values(): b.off()
        return jsonify({"status": "Sucesso"})
    except Exception as e:
        return jsonify({"status": "Erro", "msg": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
