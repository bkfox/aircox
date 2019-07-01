from django.db import models


class BaseMinMaxField:
    def __init__(self, verbose_name=None, name=None, min=None, max=None,
                 **kwargs):
        super().__init__(verbose_name, name, **kwargs)
        self.min_value = min
        self.max_value = max

    def minmax(self, value):
        return min(self.max_value, max(self.min_value, value))

    def to_python(self, value):
        return self.minmax(super().to_python(value))

    def get_prep_value(self, value):
        return super().get_prep_value(self.minmax(value))


class MinMaxField(BaseMinMaxField, models.IntegerField):
    pass

class SmallMinMaxField(BaseMinMaxField, models.SmallIntegerField):
    pass

class PositiveMinMaxField(BaseMinMaxField, models.PositiveIntegerField):
    pass

class PositiveSmallMinMaxField(BaseMinMaxField, models.PositiveSmallIntegerField):
    pass

