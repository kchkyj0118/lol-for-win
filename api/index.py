import os
import requests
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='../templates')
CORS(app)

# API Keys from environment
RIOT_API_KEY = os.environ.get("RIOT_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_latest_champion_data():
    try:
        ver_res = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()
        latest_ver = ver_res[0]
        champ_res = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{latest_ver}/data/ko_KR/champion.json").json()
        return {int(v['key']): v['name'] for k, v in champ_res['data'].items()}
    except:
        return {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/analyze', methods=['GET'])
def analyze():
    full_name = request.args.get('name')
    if not full_name or "#" not in full_name:
        return jsonify({"error": "닉네임#태그 형식으로 입력해주세요."}), 400
    
    name, tag = full_name.split("#", 1)

    try:
        # 1. Get PUUID
        acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_API_KEY}"
        acc_res = requests.get(acc_url)
        if acc_res.status_code != 200:
            return jsonify({"error": "소환사를 찾을 수 없습니다."}), 404
        puuid = acc_res.json()['puuid']

        # 2. Get Active Game
        spec_url = f"https://kr.api.riotgames.com/lol/spectator/v5/active-games/by-puuid/{puuid}?api_key={RIOT_API_KEY}"
        spec_res = requests.get(spec_url)
        if spec_res.status_code == 404:
            return jsonify({"status": "not_in_game", "message": "현재 게임 중이 아닙니다."})
        
        game_data = spec_res.json()
        champ_map = get_latest_champion_data()
        
        blue_team = []
        red_team = []
        my_team_id = 100
        
        for p in game_data['participants']:
            c_name = champ_map.get(p['championId'], "Unknown")
            if p['puuid'] == puuid:
                my_team_id = p['teamId']
            
            if p['teamId'] == 100:
                blue_team.append(c_name)
            else:
                red_team.append(c_name)

        my_champs = blue_team if my_team_id == 100 else red_team
        enemy_champs = red_team if my_team_id == 100 else blue_team

        # 3. Gemini Analysis
        prompt = f"""
        당신은 LoL 전문 코치입니다. 다음 조합을 분석해 승리 전략을 JSON으로 제시하세요.
        우리팀: {', '.join(my_champs)}
        상대팀: {', '.join(enemy_champs)}

        JSON 형식:
        {{
            "summary": "조합 요약",
            "victory_plan": "핵심 승리 플랜",
            "danger_points": "주의할 점",
            "tip": "한 줄 팁"
        }}
        """
        response = model.generate_content(prompt)
        # Handle cases where Gemini might return markdown markers
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:-3]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:-3]
            
        analysis = json.loads(cleaned_response)

        return jsonify({"status": "success", "analysis": analysis})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()
