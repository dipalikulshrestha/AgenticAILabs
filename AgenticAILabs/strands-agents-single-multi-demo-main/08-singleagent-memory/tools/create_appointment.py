import json
import uuid
from datetime import datetime
from strands import tool

@tool
def create_appointment(date: str, location: str, title: str, description: str) -> str:
    """
    Create a new personal appointment in JSON storage.

    Args:
        date (str): Date and time of the appointment (format: YYYY-MM-DD HH:MM).
        location (str): Location of the appointment.
        title (str): Title of the appointment.
        description (str): Description of the appointment.

    Returns:
        str: The ID of the newly created appointment.

    Raises:
        ValueError: If the date format is invalid.
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("Date must be in format 'YYYY-MM-DD HH:MM'")

    # Generate a unique ID
    appointment_id = str(uuid.uuid4())
    
    # Load existing appointments or create empty list
    try:
        with open("appointments.json", "r") as f:
            appointments = json.load(f)
    except FileNotFoundError:
        appointments = []
    
    # Add new appointment
    appointment = {
        "id": appointment_id,
        "date": date,
        "location": location,
        "title": title,
        "description": description
    }
    appointments.append(appointment)
    
    # Save to JSON file
    with open("appointments.json", "w") as f:
        json.dump(appointments, f, indent=2)
    
    return f"Appointment with id {appointment_id} created"