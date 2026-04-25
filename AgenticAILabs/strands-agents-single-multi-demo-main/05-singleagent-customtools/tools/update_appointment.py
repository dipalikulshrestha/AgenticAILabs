import json
from datetime import datetime
from strands import tool

@tool
def update_appointment(appointment_id: str, date: str = None, location: str = None, title: str = None, description: str = None) -> str:
    """
    Update an appointment based on the appointment ID.

    Args:
        appointment_id (str): The appointment id.
        date (str, optional): Date and time of the appointment (format: YYYY-MM-DD HH:MM).
        location (str, optional): Location of the appointment.
        title (str, optional): Title of the appointment.
        description (str, optional): Description of the appointment.

    Returns:
        str: Success or error message.
    """
    try:
        with open("appointments.json", "r") as f:
            appointments = json.load(f)
    except FileNotFoundError:
        return f"Appointment {appointment_id} does not exist"
    
    # Find appointment
    appointment = next((apt for apt in appointments if apt["id"] == appointment_id), None)
    if not appointment:
        return f"Appointment {appointment_id} does not exist"
    
    # Validate date format if provided
    if date:
        try:
            datetime.strptime(date, '%Y-%m-%d %H:%M')
        except ValueError:
            return "Date must be in format 'YYYY-MM-DD HH:MM'"
    
    # Update fields
    updated = False
    if date:
        appointment["date"] = date
        updated = True
    if location:
        appointment["location"] = location
        updated = True
    if title:
        appointment["title"] = title
        updated = True
    if description:
        appointment["description"] = description
        updated = True
    
    if not updated:
        return "No need to update your appointment, you are all set!"
    
    # Save updated appointments
    with open("appointments.json", "w") as f:
        json.dump(appointments, f, indent=2)
    
    return f"Appointment {appointment_id} updated with success"