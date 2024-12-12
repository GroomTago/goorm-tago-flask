from flask import Flask, jsonify, request
from sdk.api.message import Message
from sdk.exceptions import CoolsmsException
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
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
FLASK_DEBUG = os.getenv("FLASK_DEBUG")
FLASK_PORT = os.getenv("FLASK_PORT")

# ORM 설정
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

from extensions.database import db
db.init_app(app)

with app.app_context():
    from models.taxi_reservation import TaxiReservation
    db.create_all()

# 스케줄러 생성
scheduler = BackgroundScheduler()
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

# 문자 발송 함수
def send_sms(reservation_id):
    with app.app_context():
        reservation = TaxiReservation.query.get(reservation_id)
        if reservation:
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

# 택시 예약 문자 발송 엔드포인트
@app.route("/reservation/taxi", methods=['POST'])
def reservation_taxi():
    request_data = request.get_json()
    call_type = request.args.get("callType")

    # 현재 시간 설정 (now인 경우)
    reservation_time = datetime.now() if call_type == 'now' else datetime.strptime(request_data["reservation_time"], "%Y-%m-%dT%H:%M:%S")

    new_reservation = TaxiReservation(
        user_id=request_data["user_id"],
        starting_point=request_data["starting_point"],
        arrival_point=request_data["arrival_point"],
        reservation_phone_number=request_data["reservation_phone_number"],
        reservation_datetime=reservation_time,
        call_type=call_type
    )

    db.session.add(new_reservation)
    db.session.commit()

    # 문자 발송 (callType이 'now'인 경우 즉시 발송)
    if call_type == 'now':
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

    # 문자 예약 (callType이 'later'인 경우)
    elif call_type == 'later':
        # send_time = reservation_time - timedelta(hours=2) # 프로덕션용
        send_time = reservation_time - timedelta(minutes=5) # 개발용
        scheduler.add_job(func=send_sms, trigger='date', run_date=send_time, args=[new_reservation.id])
        print(f"SMS scheduled for: {send_time}")

        return jsonify({
            "success": True,
            "message": "Reservation saved successfully."
        }), 200


# 서버 상태 확인 엔드포인트
@app.route("/", methods=['GET'])
def server_status():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
