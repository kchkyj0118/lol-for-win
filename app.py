import os
import requests
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# API Keys from environment variables
RIOT_API_KEY = os.environ.get("RIOT_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_latest_champion_data():
    """Fetch latest champion mapping from Data Dragon"""
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

@app.route('/analyze', methods=['GET'])
def analyze():
    full_name = request.args.get('name') # Expected "Name#Tag"
    if not full_name or "#" not in full_name:
        return jsonify({"error": "닉네임#태그 형식으로 입력해주세요."}), 400
    
    name, tag = full_name.split("#", 1)

    try:
        # 1. Get PUUID (Riot ID -> PUUID)
        acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_API_KEY}"
        acc_res = requests.get(acc_url)
        if acc_res.status_code != 200:
            return jsonify({"error": "소환사를 찾을 수 없습니다. (Riot ID 확인)"}), 404
        puuid = acc_res.json()['puuid']

        # 2. Get Active Game (Spectator-v5)
        spec_url = f"https://kr.api.riotgames.com/lol/spectator/v5/active-games/by-puuid/{puuid}?api_key={RIOT_API_KEY}"
        spec_res = requests.get(spec_url)
        if spec_res.status_code == 404:
            return jsonify({"status": "not_in_game", "message": "현재 게임 중이 아닙니다."})
        if spec_res.status_code != 200:
            return jsonify({"error": "인게임 정보를 가져오는데 실패했습니다."}), 500

        # 3. Parse Team Data
        game_data = spec_res.json()
        champ_map = get_latest_champion_data()
        
        blue_team = []
        red_team = []
        my_team_id = 0
        
        for p in game_data['participants']:
            c_name = champ_map.get(p['championId'], f"Unknown({p['championId']})")
            p_name = p.get('riotId', 'Unknown')
            if p['puuid'] == puuid:
                my_team_id = p['teamId']
                p_name = f"⭐ {p_name}"
            
            if p['teamId'] == 100:
                blue_team.append(f"{p_name}({c_name})")
            else:
                red_team.append(f"{p_name}({c_name})")

        my_champs = blue_team if my_team_id == 100 else red_team
        enemy_champs = red_team if my_team_id == 100 else blue_team

        # 4. Gemini AI Analysis
        prompt = f"""
        당신은 리그 오브 레전드 전문 분석가입니다. 아래 조합을 분석하여 승리 전략을 제시하세요.
        우리 팀 조합: {', '.join(my_champs)}
        상대 팀 조합: {', '.join(enemy_champs)}

        다음 JSON 형식으로만 응답하세요:
        {{
            "summary": "전체적인 판세 요약",
            "victory_plan": "우리가 이기기 위해 반드시 해야 할 행동",
            "danger_points": "조심해야 할 상대 챔피언 및 스킬",
            "coaching_tip": "현재 판에서 가장 중요한 한 줄 조언"
        }}
        """
        response = model.generate_content(prompt)
        # Clean up Markdown artifacts if any
        json_str = response.text.strip().replace('```json', '').replace('```', '')
        analysis = json.loads(json_str)

        return jsonify({
            "status": "success",
            "game_mode": game_data.get("gameMode"),
            "analysis": analysis
        })

    except Exception as e:
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
