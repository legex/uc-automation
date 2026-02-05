"""
Query models for LDAP and Webex API operations.

This module defines Pydantic models used for validating request data
for LDAP updates and Webex migrations.
"""
from pydantic import BaseModel

class QueryModelLdap(BaseModel):
    """
    Model for LDAP contact number update requests.
    
    Attributes:
        username (str): The user's LDAP username or user ID.
        extension (str): The internal phone extension to assign.
        externalnumber (str | None): Optional external/DID number for the user.
    """
    username: str
    extension: str
    externalnumber: str | None = None

class QueryModelWebex(BaseModel):
    """
    Model for Webex user configuration update requests.
    
    Attributes:
        username (str): The user's email address in Webex.
        extension (str): The internal phone extension to assign.
        region (str): The geographical region or location for the user.
        externalnumber (str | None): Optional external/DID number for ACD setups.
    """
    username: str
    extension: str
    region: str
    externalnumber: str | None = None


class QueryModelNumberSingle(BaseModel):
    """
    Model for adding a single phone number to Webex.
    
    Attributes:
        number (str): The phone number to add.
        region (str): The region associated with the phone number.
    """
    number: str
    region: str

class QueryModelRPSingle(BaseModel):
    """
    Model for adding a single route pattern.
    
    Attributes:
        routepattern (str): The route pattern to add.
    """
    routepattern: str
    username: str

class QueryModelRPUpdate(BaseModel):
    """
    Model for updating an existing route pattern.
    
    Attributes:
        routepattern (str): The route pattern to update.
        partition (str): The partition to assign to the route pattern.
    """
    routepattern: str
    partition: str
