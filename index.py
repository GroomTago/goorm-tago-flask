from flask import Flask, jsonify, request
# coolsms
import sys
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException

# env
import os
from dotenv import load_dotenv
load_dotenv()

# cool sms
COOL_SMS_API_KEY = os.getenv("COOL_SMS_API_KEY")
COOL_SMS_API_SECRET = os.getenv("COOL_SMS_API_SECRET")

app = Flask(__name__)

@app.route("/", methods = ['GET'])
def server_status():
    data = {'status':'ok'}
    return jsonify(data)

"""
    starting_point: "출발지 도로명 주소"
    arrival_point: "도착지 도로명 주소"
    reservation_phone_number: "예약자 전화번호"
"""
@app.route("/reservation/taxi", methods=['POST'])
def reservateTaxi():
    request_data = request.get_json()
    params = {
        'to': '010-1234-5678',
        'from': '내번호',  # 가입된 번호로 전송해야 함
        'text': f'출발지 도로명 주소: {request_data["starting_point"]}, '
                f'도착지 도로명 주소: {request_data["arrival_point"]}, '
                f'예약자 전화번호: {request_data["reservation_phone_number"]}'
    }

    cool = Message(COOL_SMS_API_KEY, COOL_SMS_API_SECRET)
    response = cool.send(params)
    print(response)
    
    return jsonify({
        "success": True,
        "message": "SMS sent successfully.",
        "response": response
    }), 200
    
if __name__ == '__main__':
    app.run()