# utils/geocode.py

import requests
import os

# Kakao Maps API 설정
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"

def get_coordinates(address):
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": address
    }
    response = requests.get(KAKAO_GEOCODE_URL, headers=headers, params=params)

    print(f"Request URL: {response.url}")       # 요청 URL 출력
    print(f"Response: {response.json()}")       # 응답 내용 출력

    if response.status_code == 200:
        data = response.json()
        if data['documents']:
            location = data['documents'][0]
            return {
                "latitude": float(location["y"]),
                "longitude": float(location["x"])
            }
        else:
            return None
    else:
        return None
