from influxdb_client import Point as Point_


class Point(Point_):
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._name == other._name and self._tags == other._tags and \
               self._fields == other._fields

    def __str__(self):
        return f"{self._name}"

    def __repr__(self):
        return f"[{self.__class__.__name__}]{self.__str__()}"
