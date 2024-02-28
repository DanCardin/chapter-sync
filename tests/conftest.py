from collections.abc import Generator

import pytest
from pendulum import datetime
from responses import RequestsMock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy_model_factory.pytest import create_registry_fixture
from time_machine import TimeMachineFixture

from chapter_sync.schema import Base
from tests.factories import ModelFactory


@pytest.fixture
def responses():
    with RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(bind=engine) as session:
        yield session


@pytest.fixture(autouse=True)
def time(time_machine: TimeMachineFixture):
    time_machine.move_to(datetime(2020, 1, 1), tick=False)
    yield


@pytest.fixture
def mf_session(db: Session):
    return db


@pytest.fixture
def mf_config(db: Session):
    return {"cleanup": False}


mf_registry = create_registry_fixture(ModelFactory)
