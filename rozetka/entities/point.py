from influxdb_client import Point as Point_


class Point(Point_):
    def __str__(self):
        return f"{self._name}"

    def __repr__(self):
        return f"[{self.__class__.__name__}]{self.__str__()}"

    def __hash__(self):
        return hash(tuple(self._tags.keys()) + tuple(self._tags.values()) + tuple(self._fields.keys())
                    + tuple(self._fields.values()))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and hash(self) == hash(other)


if __name__ == '__main__':
    pass
