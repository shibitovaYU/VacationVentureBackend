import firebase_admin
from firebase_admin import credentials


def init_firebase() -> None:
    if firebase_admin._apps:
        return

    sa_path = r"D:\Учеба\8 семестр\Yu\backend\VacationVentureBackend\keys\vacationventure-service-account.json"
    if sa_path:
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred)
        return

    firebase_admin.initialize_app()
