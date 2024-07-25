"""
Runner Extensions.

Set up basic flask items for import in other modules.

*Items Setup*

:db: database
:executor: task executor

These items can be imported into other
scripts after running :obj:`scheduler.create_app`

"""

from flask_executor import Executor
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric, String
from sqlalchemy.orm import DeclarativeBase, registry
from typing_extensions import Annotated

str_120 = Annotated[str, 120]
str_200 = Annotated[str, 200]
str_8000 = Annotated[str, 8000]


class Base(DeclarativeBase):
    """Declare base types."""

    registry = registry(
        type_annotation_map={
            str_120: String(120),
            str_200: String(200),
            str_8000: String(8000),
        }
    )


db = SQLAlchemy(model_class=Base)

executor = Executor()
redis_client = FlaskRedis()
