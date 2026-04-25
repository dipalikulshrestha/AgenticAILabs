import json
from strands import tool

@tool
def list_appointments() -> str:
    """
    List all available appointments from JSON storage.
    
    Returns:
        str: the appointments available 
    """
    try:
        with open("appointments.json", "r") as f:
            appointments = json.load(f)
        return json.dumps(appointments) if appointments else "No appointment available"
    except FileNotFoundError:
        return "No appointment available"