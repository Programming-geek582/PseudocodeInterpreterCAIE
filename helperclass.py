class Assignment():
    def __init__(self, name):
        self.name = name

class ArrayAssignment(Assignment):
    def __init__(self, name, indexes):
        super().__init__(name)
        self.name = name
        self.indexes = indexes

class TypeAssignment(Assignment):
    def __init__(self, name, field):
        super().__init__(name)
        self.field = field