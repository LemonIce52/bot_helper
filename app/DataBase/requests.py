from app.DataBase.models import async_session
from app.DataBase.models import User, Event
from sqlalchemy import select, update, func, BigInteger
from sqlalchemy.sql import and_
import json

async def set_user(photo, chat_id, full_name, year,
                   phone_number, username, rating, status, passport_data) -> None:
    async with async_session() as session:
        session.add(User(
            photo = photo,
            chat_id = chat_id,
            full_name = full_name,
            year = year,
            phone_number = phone_number,
            username = username,
            rating = rating,
            status = status,
            passport_data = passport_data
        ))
        await session.commit()

async def set_event(name, description, date, method_of_work,
                    count_people, URL, status, count_days) -> None:
    async with async_session() as session:
        session.add(Event(
            count_days = count_days,
            name = name,
            description = description,
            date = date,
            method_of_work = method_of_work,
            count_people = count_people,
            URL = URL,
            status = status
        ))
        await session.commit()

async def is_event() -> bool:
    async with async_session() as session:
        event = await session.scalar(select(Event).where(Event.status == "Планируется"))
        return event is not None

async def get_event(offset = 0) -> object | None:
        async with async_session() as session:
            data = await session.scalar(select(Event).where(Event.status == "Планируется").limit(1).offset(offset))
            return data

async def get_event_view(name: str) -> object | None:
    async with async_session() as session:
        data = await session.scalar(select(Event).where(Event.name == name))
        return data

async def get_event_created() -> object | None:
        async with async_session() as session:
            data = await session.scalar(select(Event).where(Event.status == "Создается"))
            return data

async def get_events() -> object | None:
        async with async_session() as session:
            data = await session.scalar(select(Event))
            return data

async def get_events(limit = 10, offset = 0, filter = None) -> object | None:
    async with async_session() as session:
        if filter == None:
            events = await session.scalars(select(Event).limit(limit).offset(offset))
        else:
            events = await session.scalars(select(Event).where(Event.status == filter).limit(limit).offset(offset))
        return events

async def update_username_people(username, offset = 0) -> None:
    async with async_session() as session:
        username_json = json.dumps(username)
        event_name = await session.scalar(select(Event.name).where(Event.status == "Планируется").limit(1).offset(offset))
        await session.execute(update(Event).where(Event.name == event_name).values(user_name = username_json))
        await session.commit()

async def get_username_people_event(date: str) -> object | None:
    async with async_session() as session:
        username_json = await session.scalar(select(Event.user_name).where(Event.date == date))
        user_name = json.loads(username_json)
        return user_name

async def update_status_events(new_status, offset = 0) -> None:
    async with async_session() as session:
        id_update = await session.scalar(select(Event.id).where(Event.status == "Планируется").limit(1).offset(offset))
        if id_update:
            await session.execute(update(Event).where(Event.id == id_update).values(status = new_status))
            await session.commit()

async def update_profile(name_update = None, new_value = None, chat_id = None) -> None:
    async with async_session() as session:
        match name_update:
            case 'full_name':
                await session.execute(update(User).where(User.chat_id == chat_id).values(full_name = new_value))
            case 'birthday':
                await session.execute(update(User).where(User.chat_id == chat_id).values(year = new_value))
            case 'phone_number':
                await session.execute(update(User).where(User.chat_id == chat_id).values(phone_number = new_value))
            case 'username':
                await session.execute(update(User).where(User.chat_id == chat_id).values(username = new_value))
            case 'pass_data':
                await session.execute(update(User).where(User.chat_id == chat_id).values(passport_data = new_value))
        await session.commit()

async def update_status_planing() -> None:
    async with async_session() as session:
        await session.execute(update(Event).where(Event.status == "Создается").values(status = "Планируется"))
        await session.commit()

async def count_events(filter = None) -> int:
    async with async_session() as session:
        count_event = 0
        if filter == None:
            count_event = await session.scalar(func.count(Event.id))
        else:
            events = await session.scalars(select(Event).where(Event.status == filter))
            for number, event in enumerate(events, start=1):
                count_event = number
        return count_event

async def count_event_where_planing() -> int:
    async with async_session() as session:
        planing_event = await session.scalars(select(Event.id).where(Event.status == "Планируется"))
        count = 0
        for new_count, planing_events in enumerate(planing_event, start=1):
            count = new_count
        return count

async def is_user(chat_id) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.chat_id == chat_id))
        return user is not None

async def is_owner(chat_id) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.chat_id == chat_id and User.status == "Владелец"))
        return user is not None

async def is_worker(chat_id) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.chat_id == chat_id and User.status != "Модерация"))
        return user is not None

async def update_rating_up(chat_id) -> None:
    async with async_session() as session:
        await session.execute(update(User).where(User.chat_id == chat_id).values(rating = User.rating + 1))
        await session.commit()

async def update_rating_up_value(chat_id, value) -> None:
    async with async_session() as session:
        await session.execute(update(User).where(User.chat_id == chat_id).values(rating = User.rating + value))
        await session.commit()

async def update_rating_down(chat_id) -> None:
    async with async_session() as session:
        await session.execute(update(User).where(User.chat_id == chat_id).values(rating = User.rating - 1))
        await session.commit()

async def update_rating_down_value(chat_id, value) -> None:
    async with async_session() as session:
        await session.execute(update(User).where(User.chat_id == chat_id).values(rating = User.rating - value))
        await session.commit()

async def count_user(filter = None) -> int:
    async with async_session() as session:
        count_user = 0
        if filter == None:
            count_user = await session.scalar(func.count(User.id))
        else:
            users = await session.scalars(select(User).where(User.status == filter))
            for number, user in enumerate(users, start=1):
                count_user = number
        return count_user

async def get_id_owner() -> BigInteger:
    async with async_session() as session:
        chat_id = await session.scalar(select(User.chat_id).where(User.status == 'Владелец').limit(1))
        return chat_id

async def get_status(chat_id: BigInteger) -> str:
    async with async_session() as session:
        status = await session.scalar(select(User.status).where(User.chat_id == chat_id))
        return status

async def update_status(chat_id: BigInteger, new_status: str) -> None:
    async with async_session() as session:
        await session.execute(update(User).where(User.chat_id == chat_id).values(status = new_status))
        await session.commit()

async def get_profile(chat_id: BigInteger) -> object | None:
        async with async_session() as session:
            data = await session.scalar(select(User).where(User.chat_id == chat_id))
            return data

async def get_profiles(limit = 10, offset = 0, filter = None) -> object | None:
    async with async_session() as session:
        if filter == None:
            profiles = await session.scalars(select(User).limit(limit).offset(offset))
        else:
            profiles = await session.scalars(select(User).where(User.status == filter).limit(limit).offset(offset))
        return profiles

async def get_profile_view(full_name: str) -> object | None:
    async with async_session() as session:
        profile = await session.scalar(select(User).where(User.full_name == full_name))
        return profile

async def get_profile_view_username(username: str) -> object | None:
    async with async_session() as session:
        profile = await session.scalar(select(User).where(User.username == username))
        return profile

async def get_profile_moderation() -> object | None:
    async with async_session() as session:
        data = await session.scalar(select(User).where(User.status == 'Модерация').limit(1))
        return data

async def get_worker_id() -> object | None:
    async with async_session() as session:
        chat_id = await session.scalars(select(User.chat_id).where(and_(User.status != 'Владелец', User.status != 'Модерация')))
        return chat_id

async def get_profile_for_user_name(user_name: str) -> object | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.username == user_name))
        return user

async def delete_profile(chat_id: BigInteger) -> None:
    async with async_session() as session:
        delete_user = await session.scalar(select(User).where(User.chat_id == chat_id))
        if delete_user:
            await session.delete(delete_user)
            await session.commit()
        users = await session.scalars(select(User))
        if users:
            for new_id, user in enumerate(users, start=1):
                await session.execute(update(User).where(User.full_name == user.full_name).values(id = new_id))
            
            await session.commit()