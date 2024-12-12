from flask import Flask, jsonify, request
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import atexit
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Flask 앱 생성
app = Flask(__name__)

# 환경 변수 설정
IS_DEV = os.getenv("IS_DEV")
COOL_SMS_API_KEY = os.getenv("COOL_SMS_API_KEY")
COOL_SMS_API_SECRET = os.getenv("COOL_SMS_API_SECRET")
SEND_PHONE_NUMBER = os.getenv("SEND_PHONE_NUMBER")
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")

# ORM 설정
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

from extensions.database import db
db.init_app(app)

with app.app_context():
    from models.taxi_reservation import TaxiReservation
    db.create_all()

# 데이터베이스 연결 확인 함수
def check_database_connection():
    try:
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            print("Database connection successful")
    except SQLAlchemyError as e:
        print(f"Database connection Failed: {e}")

# 예약 문자 발송 함수
def send_scheduled_sms():
    with app.app_context():
        reservations = TaxiReservation.query.filter(
            TaxiReservation.call_type == 'later',
            TaxiReservation.reservation_datetime <= datetime.now()
        ).all()
        
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

# 스케줄러 설정
scheduler = BackgroundScheduler()
scheduler.add_job(func=send_scheduled_sms, trigger='cron', hour='0,3,6,9,12,15,18,21', minute=0)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

check_database_connection()

@app.route("/", methods=['GET'])
def server_status():
    return jsonify({'status': 'ok'})

# 택시 예약 문자 발송 엔드포인트
@app.route("/reservation/taxi", methods=['POST'])
def reservation_taxi():
    request_data = request.get_json()
    call_type = request.args.get("callType")

    new_reservation = TaxiReservation(
        user_id=request_data["user_id"],
        starting_point=request_data["starting_point"],
        arrival_point=request_data["arrival_point"],
        reservation_phone_number=request_data["reservation_phone_number"],
        reservation_datetime=datetime.strptime(request_data["reservation_time"], "%Y-%m-%dT%H:%M:%S") if call_type == 'later' else datetime.now(),
        call_type=call_type
    )

    db.session.add(new_reservation)
    db.session.commit()

    # 문자 발송
    params = {
        'to': request_data["reservation_phone_number"],
        'from': SEND_PHONE_NUMBER,
        'text': f'출발지: {request_data["starting_point"]}, '
                f'도착지: {request_data["arrival_point"]}'
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
    app.run(debug=IS_DEV)
