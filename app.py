from flask import Flask, jsonify, request
# coolsms
import sys
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
# ORM
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
# Scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import atexit

# env
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

IS_DEV = os.getenv("IS_DEV")
# cool sms
COOL_SMS_API_KEY = os.getenv("COOL_SMS_API_KEY")
COOL_SMS_API_SECRET = os.getenv("COOL_SMS_API_SECRET")
SEND_PHONE_NUMBER = os.getenv("SEND_PHONE_NUMBER")
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS= os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
# ORM
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
db = SQLAlchemy(app)

# 분리 필요 함수 Start
# 데이터베이스 연결 확인 함수 (TODO: 리팩토링)
def check_database_connection():
    try:
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            print("Database connection successful")
    except SQLAlchemyError as e:
        print(f"Database connection Failed: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_scheduled_sms, trigger='cron', hour=0, minute=0)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())
# 예약 문자 발송
def send_scheduled_sms():
     reservations = TaxiReservation.query.filter(
          TaxiReservation.reservation_datetime <= datetime.now()
     ).all
     for reservation in reservations:
          params = {
               'to': reservation.reservation_phone_number,
               'from': SEND_PHONE_NUMBER,
               'text': f'출발지: {reservation.starting_point}, '
                        f'도착지: {reservation.arrival_point}'
          }
          cool = Message(COOL_SMS_API_KEY, COOL_SMS_API_SECRET)
          response = cool.send(params)
          print(response)

          db.session.delete(reservation)
          db.session.commit()
# 분리 필요 함수 End
check_database_connection()

@app.route("/", methods = ['GET'])
def server_status():
    data = {'status':'ok'}
    return jsonify(data)

# 택시 예약 문자 즉시발송
"""
    starting_point: "출발지 도로명 주소"
    arrival_point: "도착지 도로명 주소"
    reservation_phone_number: "예약자 전화번호"
"""
@app.route("/reservation/taxi/now", methods=['POST'])
def reservation_taxi_now():
    request_data = request.get_json()
    params = {
        'to': '010-1234-5678',
        'from': SEND_PHONE_NUMBER,  # 가입된 번호로 전송해야 함
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


# 택시 예약 문자 예약발송
# 중복되는 코드 추후 리팩토링 예정
"""
    starting_point: "출발지 도로명 주소"
    arrival_point: "도착지 도로명 주소"
    reservation_time: "택시 예약 시간" (YYYY-MM-DDTHH:MM:SS)
    reservation_phone_number: "예약자 전화번호"
    
"""
@app.route("/reservation/taxi/later", methods=['POST'])
def reservation_taxi_later():
        # request_data = request.get_json()
        # params = {
        #      'to':'010-1234-5678',
        #      'from': SEND_PHONE_NUMBER,
        #      'text': f'출발지 도로명 주소: {request_data["starting_point"]}, '
        #         f'도착지 도로명 주소: {request_data["arrival_point"]}, '
        #         f'예약자 전화번호: {request_data["reservation_phone_number"]}'
        # }
        request_data = request.get_json()
        new_reservation = TaxiReservation(
            starting_point=request_data["starting_point"],
            arrival_point=request_data["arrival_point"],
            reservation_phone_number=request_data["reservation_phone_number"],
            reservation_datetime=datetime.strptime(request_data["reservation_time"], "%Y-%m-%dT%H:%M:%S")
        )
        db.session.add(new_reservation)
        db.session.commit()

        cool = Message(COOL_SMS_API_KEY, COOL_SMS_API_SECRET)
        response = cool.send(params)
        print(response)

        return jsonify({
            "success": True,
            "message": "SMS sent successfully.",
            "response": response
        }), 200
    
if __name__ == '__main__':
    app.run(debug=IS_DEV)