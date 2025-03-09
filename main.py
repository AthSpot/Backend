from s3_database import S3Database
import os

# Konfiguracja AWS
BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME', 'twoja-nazwa-bucketu')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Inicjalizacja bazy danych S3
db = S3Database(bucket_name=BUCKET_NAME, region_name=AWS_REGION)



def save_user(user_id, user_data):
    """Zapisz dane użytkownika do S3"""
    db.save_data(f"users/{user_id}", user_data)


def get_user(user_id):
    """Pobierz dane użytkownika z S3"""
    return db.load_data(f"users/{user_id}")


def delete_user(user_id):
    """Usuń dane użytkownika z S3"""
    db.delete_data(f"users/{user_id}")


def list_users():
    """Wyświetl listę wszystkich użytkowników"""
    return db.list_keys(prefix="users/")



# Przykład użycia:
if __name__ == "__main__":
    user = {
        "name": "Jan Kowalski",
        "email": "jan@example.com",
        "age": 30
    }

    save_user("user123", user)
    retrieved_user = get_user("user123")
    print(f"Pobrano użytkownika: {retrieved_user}")

    all_users = list_users()
    print(f"Lista użytkowników: {all_users}")