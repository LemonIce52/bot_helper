from app.DataBase.models import async_session, User
from random import randint
import faker
import asyncio

async def create_fake_user(full_name, year,
                   phone_number, username, rating, status):
    async with async_session() as session:
        session.add(User(
            full_name = full_name,
            year = year,
            phone_number = phone_number,
            username = username,
            rating = rating,
            status = status,
        ))
        await session.commit()

def fake(count):
    fake = faker.Faker("de_DE")
    users = []
    status = ['Начинающий', 'Маршал', 'Основной состав']
    for i in range(count):
        count = randint(0, 2)
        users.append(
            {
                "full_name": fake.name(),
                "year": fake.building_number(),
                "phone_number": fake.building_number(),
                "username": fake.last_name(),
                "rating": 0,
                "status": status[count]
            }
            )
    
    return users

async def main():
    users = fake(20)
    for user in users:
        await create_fake_user(user["full_name"], user["year"], user["phone_number"], f'@{user["username"]}', user["rating"], user["status"])
    print("зкончено")

asyncio.run(main())