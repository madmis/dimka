from peewee import *

database = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = database


class Ticker(BaseModel):
    pair = CharField(max_length=10)
    high = DecimalField(max_digits=15, decimal_places=10)
    low = DecimalField(max_digits=15, decimal_places=10)
    avg = DecimalField(max_digits=15, decimal_places=10)
    last = DecimalField(max_digits=15, decimal_places=10)
    buy = DecimalField(max_digits=15, decimal_places=10)
    sell = DecimalField(max_digits=15, decimal_places=10)
    vol = DecimalField(max_digits=15, decimal_places=5)
    vol_cur = DecimalField(max_digits=15, decimal_places=5)
    updated = DateTimeField(index=True)
    updated_timestamp = TimestampField(utc=True, index=True)

    class Meta:
        order_by = ('-updated_timestamp',)
        indexes = (
            # create a unique
            (('updated_timestamp', 'pair'), True),
        )


class OrderInfo(BaseModel):
    pair = CharField(max_length=10)
    order_type = CharField(max_length=10)
    amount = DecimalField(max_digits=15, decimal_places=10)
    rate = DecimalField(max_digits=15, decimal_places=10)
    parent_order = ForeignKeyField("self", null=True)
    created = DateTimeField(index=True)
    created_timestamp = TimestampField(utc=True, index=True)

    class Meta:
        order_by = ('-created_timestamp',)
