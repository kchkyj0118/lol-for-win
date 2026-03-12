import os
import requests
import json
import google.generativeai as genai
from datetime import datetime

# API Keys from environment (GitHub Secrets)
RIOT_API_KEY = os.environ.get("RIOT_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Target Player (GitHub Secrets RIOT_NAME, RIOT_TAG)
RIOT_NAME = os.environ.get("RIOT_NAME", "내닉네임")
RIOT_TAG = os.environ.get("RIOT_TAG", "KR1")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_latest_champion_data():
    """Fetch latest champion mapping from Data Dragon"""
    try:
        ver_res = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()
        latest_ver = ver_res[0]
        champ_res = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{latest_ver}/data/ko_KR/champion.json").json()
        return {int(v['key']): v['name'] for k, v in champ_res['data'].items()}, latest_ver
    except:
        return {}, "14.5.1"

def analyze_game():
    champ_map, version = get_latest_champion_data()
    
    try:
        # 1. Get PUUID
        acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{RIOT_NAME}/{RIOT_TAG}?api_key={RIOT_API_KEY}"
        acc_res = requests.get(acc_url)
        if acc_res.status_code != 200:
            return {"status": "error", "message": f"User {RIOT_NAME}#{RIOT_TAG} not found."}
        puuid = acc_res.json()['puuid']

        # 2. Get Active Game
        spec_url = f"https://kr.api.riotgames.com/lol/spectator/v5/active-games/by-puuid/{puuid}?api_key={RIOT_API_KEY}"
        spec_res = requests.get(spec_url)
        
        if spec_res.status_code == 404:
            return {"status": "not_in_game", "message": "현재 게임 중이 아닙니다.", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        game_data = spec_res.json()
        blue_team, red_team = [], []
        my_team_id = 100
        
        for p in game_data['participants']:
            c_name = champ_map.get(p['championId'], f"Unknown({p['championId']})")
            if p['puuid'] == puuid:
                my_team_id = p['teamId']
            
            if p['teamId'] == 100:
                blue_team.append(c_name)
            else:
                red_team.append(c_name)

        my_champs = blue_team if my_team_id == 100 else red_team
        enemy_champs = red_team if my_team_id == 100 else blue_team

        # 3. Gemini AI Analysis
        prompt = f"""
        당신은 리그 오브 레전드 챌린저급 분석가입니다. 아래 조합을 정밀 분석해 승리 전략을 JSON 형식으로 작성하세요.
        우리 팀 조합: {', '.join(my_champs)}
        상대 팀 조합: {', '.join(enemy_champs)}

        JSON 형식으로만 답변하세요:
        {{
            "summary": "전반적인 판세 요약",
            "victory_plan": "우리가 승리하기 위한 핵심 전략 3가지",
            "danger_skills": "조심해야 할 상대 스킬 2개",
            "one_line_tip": "지금 즉시 수행해야 할 한 줄 조언"
        }}
        """
        response = model.generate_content(prompt)
        # Clean up JSON from response text
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        analysis = json.loads(clean_text)

        return {
            "status": "success",
            "game_mode": game_data.get("gameMode"),
            "my_team": my_champs,
            "enemy_team": enemy_champs,
            "analysis": analysis,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = analyze_game()
    with open("strategy.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Strategy updated successfully.")
