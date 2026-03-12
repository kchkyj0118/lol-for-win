import os
import requests
import json
from datetime import datetime

# Riot API Configuration
API_KEY = os.environ.get("RIOT_API_KEY")
REGION = "kr"
ROUTING = "asia"

# Basic Champion ID to Name Mapping (Data Dragon 14.5.1)
CHAMP_MAP = {
    1: "애니", 2: "올라프", 3: "갈리오", 4: "트위스티드 페이트", 5: "신 짜오", 6: "우르곳", 7: "르블랑", 8: "블라디미르", 9: "피들스틱", 10: "케일",
    11: "마스터 이", 12: "알리스타", 13: "라이즈", 14: "사이온", 15: "시비르", 16: "소라카", 17: "티모", 18: "트리스타나", 19: "워윅", 20: "누누와 윌럼프",
    21: "미스 포츈", 22: "애쉬", 23: "트린다미어", 24: "잭스", 25: "모르가나", 26: "질리언", 27: "신지드", 28: "이블린", 29: "트위치", 30: "카서스",
    31: "초가스", 32: "아무무", 33: "람머스", 34: "애니비아", 35: "샤코", 36: "문도 박사", 37: "소나", 38: "카사딘", 39: "이렐리아", 40: "잔나",
    41: "갱플랭크", 42: "코르키", 43: "카르마", 44: "타릭", 45: "베이가", 48: "트런들", 50: "스웨인", 51: "케이틀린", 53: "블리츠크랭크", 54: "말파이트",
    55: "카타리나", 56: "녹턴", 57: "마오카이", 58: "레넥톤", 59: "자르반 4세", 60: "엘리스", 61: "오리아나", 62: "오공", 63: "브랜드", 64: "리 신",
    67: "베인", 68: "럼블", 69: "카시오페아", 72: "스카너", 74: "하이머딩거", 75: "나서스", 76: "니달리", 77: "우디르", 78: "뽀삐", 79: "그라가스",
    80: "판테온", 81: "이즈리얼", 82: "모데카이저", 83: "요릭", 84: "아칼리", 85: "케넨", 86: "가렌", 89: "레오나", 90: "말자하", 91: "탈론",
    92: "리븐", 96: "코그모", 98: "쉔", 99: "럭스", 101: "제라스", 102: "쉬바나", 103: "아리", 104: "그레이브즈", 105: "피즈", 106: "볼리베어",
    107: "렝가", 110: "바루스", 111: "노틸러스", 112: "빅토르", 113: "세주아니", 114: "피오라", 115: "직스", 117: "룰루", 119: "드레이븐", 120: "헤카림",
    121: "카직스", 122: "다리우스", 126: "제이스", 127: "리산드라", 131: "다이애나", 133: "퀸", 134: "신드라", 136: "아우렐리온 솔", 141: "케인", 142: "조이",
    143: "자이라", 145: "카이사", 147: "세라핀", 150: "나르", 154: "자크", 157: "야스오", 161: "벨코즈", 163: "탈리야", 164: "카밀", 166: "아크샨",
    201: "브라움", 202: "진", 203: "킨드레드", 222: "징크스", 223: "탐 켄치", 233: "브라이어", 234: "비에고", 235: "세나", 236: "루시안", 238: "제드",
    240: "클레드", 245: "에코", 246: "키아나", 254: "바이", 266: "아트록스", 267: "나미", 268: "아지르", 350: "유미", 360: "사미라", 412: "쓰레쉬",
    420: "일라오이", 421: "렉사이", 427: "아이번", 429: "칼리스타", 432: "바드", 497: "라칸", 498: "자야", 516: "오른", 517: "사일러스", 518: "니코",
    523: "아펠리오스", 526: "렐", 555: "파이크", 711: "벡스", 777: "요네", 875: "세트", 876: "릴리아", 887: "그웬", 888: "레나타 글라스크", 895: "니라",
    897: "크산테", 901: "스몰더", 902: "밀리오", 910: "흐웨이", 950: "나피리"
}

def generate_coach_strategy(blue_champs, red_champs, my_team):
    """Simple AI-like heuristic strategy generator"""
    our_team = blue_champs if my_team == 100 else red_champs
    enemy_team = red_champs if my_team == 100 else blue_champs
    
    plan = f"우리 팀({', '.join(our_team)})은 초반 주도권을 바탕으로 오브젝트 교전에 집중해야 합니다. "
    plan += f"상대 팀({', '.join(enemy_team)})의 후반 포텐셜이 높으므로 25분 이전에 승기를 굳히는 것이 핵심입니다."
    
    skills = [f"{enemy_team[0]}의 궁극기 타이밍을 주의하세요.", "대규모 한타 시 적 주요 딜러의 생존기를 먼저 소모시켜야 합니다."]
    lines = ["바텀 라인의 압박을 통해 첫 드래곤을 안정적으로 확보하세요.", "미드 정글의 2:2 교전에서 승리하는 팀이 전체 주도권을 가져갑니다."]
    
    return {
        "victory_plan": plan,
        "watch_out": skills,
        "focus_line": lines,
        "blue_team": blue_champs,
        "red_team": red_champs,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    # Example Target: 내닉네임#KR1 (환경 변수 RIOT_NAME, RIOT_TAG 사용 권장)
    name = os.environ.get("RIOT_NAME", "내닉네임")
    tag = os.environ.get("RIOT_TAG", "KR1")
    
    # 1. Get PUUID
    acc_url = f"https://{ROUTING}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={API_KEY}"
    res = requests.get(acc_url)
    if res.status_code != 200:
        print("User not found")
        return

    puuid = res.json()['puuid']
    
    # 2. Get Active Game
    spec_url = f"https://{REGION}.api.riotgames.com/lol/spectator/v5/active-games/by-puuid/{puuid}?api_key={API_KEY}"
    res = requests.get(spec_url)
    
    strategy = {}
    if res.status_code == 200:
        game_data = res.json()
        blue_champs = [CHAMP_MAP.get(p['championId'], "Unknown") for p in game_data['participants'] if p['teamId'] == 100]
        red_champs = [CHAMP_MAP.get(p['championId'], "Unknown") for p in game_data['participants'] if p['teamId'] == 200]
        my_team = next(p['teamId'] for p in game_data['participants'] if p['puuid'] == puuid)
        
        strategy = generate_coach_strategy(blue_champs, red_champs, my_team)
        strategy["status"] = "IN_GAME"
    else:
        strategy = {
            "status": "NOT_IN_GAME",
            "message": "현재 게임 중이 아닙니다. 게임이 시작되면 AI 코칭이 활성화됩니다.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    with open("strategy.json", "w", encoding="utf-8") as f:
        json.dump(strategy, f, ensure_ascii=False, indent=2)
    print("Strategy updated.")

if __name__ == "__main__":
    main()
