from copy import copy
from error import Error


class DataType():
    """Super class for all data types"""

    def __init__(self, data_type, referee_name=None, reference_type='BYVAL', default=None):
        self.data_type = data_type
        self.referee_name = referee_name
        self.reference_type = reference_type
        self.default = default
# START: Variable


class VariableType(DataType):
    """Declares and initally assigns to all variables

    Arguments:
        DataType {DataType} -- This class inherits its __init__() function from it
    """

    def __init__(self, data_type, referee_name=None, reference_type='BYVAL', default=None):
        """Initializes a variable

        Arguments:
            data_type {str} -- The data type of the object being initialized

        Keyword Arguments:
            referee_name {str} -- The name of the variable this instance is being copied from in the parent scope (default: {None})
            reference_type {str} -- The type of reference being used when passing this instance as a parameter (default: {'BYVAL'})
        """
        super().__init__(data_type, referee_name, reference_type, default)

    def declare(self):
        """Declares a variable

        Returns:
            Variable -- The value of the instance encapsulated inside the Variable class
        """
        return Variable(self.default)


class Variable():
    """Class for Variable used in the VariableType class"""

    def __init__(self, default):
        """Assigns a value (None) to a Variable"""
        self.value = default

    def assign(self, value):
        """Assigns a value to a Variable

        Arguments:
            value {int, str, bool, float} -- The value to be stored in a Variable
        """

        # [0] is being used here because value is a list
        self.value = value[0]

# END: Variable

# START: Constant


class ConstantType(DataType):
    """Declares and initally assigns to all constants

    Arguments:
        DataType {DataType} -- This class inherits its __init__() function from it
    """

    def __init__(self, data_type='CONSTANT'):
        """Initializes a constant

        Arguments:
            data_type {str} -- The data type of the object being initialized

        Keyword Arguments:
            referee_name {str} -- The name of the variable this instance is being copied from in the parent scope (default: {None})
            reference_type {str} -- The type of reference being used when passing this instance as a parameter (default: {'BYVAL'})
        """
        super().__init__(data_type)

    def declare(self, value=None):
        """Declares a constant

        Returns:
            Constant -- The value of the instance encapsulated inside the Constant class
        """
        return Constant(value)


class Constant():
    def __init__(self, value):
        """Decalares and assigns a value to a constant

        Arguments:
            value {int, str, bool, float} -- Assign a value to Constant
        """
        self.value = value

# END: Constant

# START: Array


class ArrayType(DataType):
    """Declares and initally assigns to all arrays

    Arguments:
        DataType {DataType} -- This class inherits its __init__() function from it
    """

    def __init__(self, dimensions, data_type, referee_name=None, reference_type='BYVAL', default=None):
        """Initializes an array

        Arguments:
            dimensions {list{list{int}}} -- The dimensions of the array stored as a 2D list with upper and lower bounds
            data_type {str} -- The data type of the object being initialized

        Keyword Arguments:
            referee_name {str} -- The name of the variable this instance is being copied from in the parent scope (default: {None})
            reference_type {str} -- The type of reference being used when passing this instance as a parameter (default: {'BYVAL'})
        """
        super().__init__(data_type, referee_name, reference_type, default)
        self.dimensions = dimensions

    def declare(self):
        """Declares an array

        Returns:
            Array -- The value of the instance encapsulated inside the Array class
        """
        layers = len(self.dimensions)
        deep_layer_indexes = {}      # The array/index at the current index
        shallow_layer_indexes = {}     # The array/index at the previous index

        # Start from the deepest layer and work up till the first layer
        for i in range(layers - 1, -1, -1):
            # Checks if its the deepest layer
            if i + 1 == layers:
                for j in range(self.dimensions[i][0], self.dimensions[i][1] + 1):
                    deep_layer_indexes[j] = self.default
            else:
                # Append deep layer to the shallow layer
                shallow_layer_indexes = copy(deep_layer_indexes)
                deep_layer_indexes = {}

                for j in range(self.dimensions[i][0], self.dimensions[i][1] + 1):
                    deep_layer_indexes[j] = shallow_layer_indexes

        return Array(deep_layer_indexes)


class Array():
    def __init__(self, value):
        """Decalares and assigns a value to an array

        Arguments:
            value {int, str, bool, float} -- Assign a value to Array
        """
        self.value = value

    def assign(self, data):
        """Assigns a value to a Variable

        Arguments:
            data {tuple} -- The data to be stored in an Array
        """
        value = data[0]
        if type(value) is not list:
            print(value)
            print(data)
            indexes = data[1]
            array_indexes = self.value

            for i in range(len(indexes) - 1):
                try:
                    array_indexes = array_indexes.get(indexes[i])
                except:
                    # TODO November 07, 2019: Find a way to output the name of the array
                    Error().index_error('Index out of bounds')

            array_indexes[indexes[-1]] = value
        else:
            # TODO November 09, 2019: Compare both arrays and see if their ranks and length match up
            self.value = value

# END: Array

# START: Type


class TypeType(DataType):
    def __init__(self, fields, data_type, referee_name=None, reference_type='BYVAL'):
        """Initializes a type

        Arguments:
            scope {Scope} -- The scope where the fields of the type were declared
            data_type {str} -- The data type of the object being initialized

        Keyword Arguments:
            referee_name {str} -- The name of the variable this instance is being copied from in the parent scope (default: {None})
            reference_type {str} -- The type of reference being used when passing this instance as a parameter (default: {'BYVAL'})
        """
        self.fields = fields
        default = {}
        for field in fields.keys():
            default[field] = fields[field].declare()

        super().__init__(data_type, referee_name, reference_type, default)

    def declare(self):
        """Declares an array

        Returns:
            Type -- The value of the instance encapsulated inside the Type class
        """
        field_values = {}
        for field in self.fields.items():
            field_values[field[0]] = field[1].declare()

        return Type(field_values)


class Type():
    def __init__(self, name, value):
        self.value = value

    def assign(self, data):
        value = data[0]
        field = data[1]

        self.value[field].value = value

    # END: Type
