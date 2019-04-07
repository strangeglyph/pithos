import enum

import sqlalchemy
from sqlalchemy import Column, ForeignKey, BigInteger, Enum, Boolean, Integer, String, Date, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

__session: sqlalchemy.orm.Session = None
Base = declarative_base()


def get_session(engine_override=None) -> sqlalchemy.orm.Session:
    global __session
    if not __session:
        engine = engine_override if engine_override else sqlalchemy.create_engine("sqlite:///pithos.db")
        engine.connect()
        __session = sessionmaker(bind=engine)()
        Base.metadata.create_all(engine)
    return __session


class DelegationType(enum.Enum):
    TRANSITIVE = 0
    FIXED = 1


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    accepts_delegates = Column(Boolean, nullable=False)
    delegate_id = Column(BigInteger, ForeignKey("users.id"))
    delegation_type = Column(Enum(DelegationType))

    delegate = relationship("User", remote_side=[id], backref="constituents")
    votes = relationship("Vote", back_populates="user", cascade="all, delete, delete-orphan")

    ck_if_delegate_is_set_delegation_type_is_set = CheckConstraint('delegate_id IS NULL OR delegation_type IS NOT NULL',
                                                                   name='ck_if_delegate_is_set_delegation_type_is_set')


class Motion(Base):
    __tablename__ = 'motions'

    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    expires = Column(Date, nullable=False)
    options = relationship("MotionOptions", back_populates="motion", cascade="all, delete, delete-orphan")
    votes = relationship("Vote", back_populates="motion", cascade="all, delete, delete-orphan")


class MotionOptions(Base):
    __tablename__ = 'motion_options'

    option_no = Column(Integer, primary_key=True)
    motion_id = Column(BigInteger, ForeignKey("motions.id"), primary_key=True)
    description = Column(String, nullable=False)
    motion = relationship("Motion", back_populates="options")


class Vote(Base):
    __tablename__ = 'votes'

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    motion_id = Column(Integer, ForeignKey("motions.id"), primary_key=True)
    selection = Column(Integer, nullable=False)
    motion = relationship("Motion", back_populates="votes")
    user = relationship("User", back_populates="votes")


#
# TESTS
#


def test_constituent_backref():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    session = get_session(engine)

    user_a = User()
    user_b = User()
    user_c = User()
    user_d = User()

    session.add_all([user_a, user_b, user_c, user_d])

    user_a.delegate = user_b
    user_b.delegate = user_d
    user_c.delegate = user_d

    assert len(user_a.constituents) == 0
    assert len(user_b.constituents) == 1
    assert len(user_c.constituents) == 0
    assert len(user_d.constituents) == 2

    user_a.delegate = user_c
    assert len(user_b.constituents) == 0
    assert len(user_c.constituents) == 1


def test_foo():
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    session = get_session(engine)

    user_a = User(id=1)
    user_b = User(id=2)
    motion_1 = Motion(id=1)
    motion_2 = Motion(id=2)

    session.add_all([user_a, user_b, motion_1, motion_2])

    motion_1.options.append(MotionOptions(option_no=1, motion_id=1, description="Do the thing"))
    motion_1.options.append(MotionOptions(option_no=2, motion_id=1, description="Don't do the thing"))

    motion_2.options.append(MotionOptions(option_no=1, motion_id=2, description="Flux the quantum disentagler"))
    motion_2.options.append(MotionOptions(option_no=2, motion_id=2, description="Disentagle the flux quantum"))
    motion_2.options.append(MotionOptions(option_no=3, motion_id=2, description="Quantify the disentagling flux"))

    assert len(motion_1.options) == 2
    assert len(motion_2.options) == 3

    vote_a1 = Vote(user=user_a, motion=motion_1, selection=2)
    vote_a2 = Vote(user=user_a, motion=motion_2, selection=1)
    vote_b1 = Vote(user=user_b, motion=motion_1, selection=2)

    assert len(user_a.votes) == 2
    assert len(user_b.votes) == 1
    assert len(motion_1.votes) == 2
    assert len(motion_2.votes) == 1
