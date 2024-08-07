from sqlalchemy import BigInteger, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///app/DataBase/db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int] = mapped_column()
    year: Mapped[int] = mapped_column()
    full_name: Mapped[str] = mapped_column()
    phone_number: Mapped[str] = mapped_column()
    username: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    chat_id = mapped_column(BigInteger)
    photo = mapped_column(LargeBinary)
    passport_data = mapped_column(LargeBinary)

class Event(Base):
    __tablename__ = 'events'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    count_days: Mapped[int] = mapped_column()
    count_people: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    date: Mapped[str] = mapped_column()
    method_of_work: Mapped[str] = mapped_column()
    URL: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    user_name: Mapped[str] = mapped_column()
    
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)