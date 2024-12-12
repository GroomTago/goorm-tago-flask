# utils/geocode.py

import requests
import os
from math import radians, sin, cos, sqrt, atan2

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

def haversine(lat1, lon1, lat2, lon2):
    """Haversine 공식을 사용해 두 지점 간의 거리(km)를 계산"""
    R = 6371.0  # 지구 반지름 (km)

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance