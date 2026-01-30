"""
Python file that needs black formatting.

This fixture is syntactically valid but poorly formatted.
"""

from typing import Dict, List


def unformatted_function(param1,param2,param3):
    """Function with bad formatting."""
    if param1=='value' and param2=='another' and param3=='third':
        result={'key1': 'value1', 'key2': 'value2', 'key3': 'value3', 'key4': 'value4'}
        return result
    else:
        return None


class UnformattedClass:
    """Class needing formatting."""
    def __init__(self,name: str,age: int,email: str,phone: str,address: str):
        self.name=name
        self.age=age
        self.email=email
        self.phone=phone
        self.address=address

    def process(self,data: Dict[str,str])->List[str]:
        """Process data with poor formatting."""
        results=[]
        for key,value in data.items():
            if value is not None and len(value)>0:
                processed=f"{key}: {value}"
                results.append(processed)
        return results


# Dictionary with inconsistent formatting
config = {'setting1':'value1','setting2':'value2','setting3':{'nested1':'n1','nested2':'n2'}}

# List with poor formatting
numbers = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]

# Function call with poor formatting
result = unformatted_function('arg1','arg2','arg3')
