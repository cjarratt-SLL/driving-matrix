import pytest
from sqlmodel import Session, SQLModel, create_engine

from tests.fixtures import build_seed_records


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as db_session:
        records = build_seed_records()
        db_session.add_all(records["residents"])
        db_session.add_all(records["drivers"])
        db_session.add_all(records["vehicles"])
        db_session.add_all(records["locations"])
        db_session.add_all(records["trips"])
        db_session.commit()
        yield db_session
