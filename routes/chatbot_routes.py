from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.chat import (
    login,
    search_providers,
    book_appointment,
    provider_sched,
    search_provider,
    fetch_user_appointments,
    cancel_user_appointment
)

chatbot_bp = Blueprint("chatbot_bp", __name__)

user_context = {}

def format_datetime_readable(date_string):
    """
    Formats a datetime string into a more readable format.
    Args:
        date_string (str): Datetime string.
    Returns:
        str: Formatted datetime string (e.g., "12/01/2024, 10:00 AM").
    """
    try:
        # Parse the datetime string as ISO 8601
        dt = datetime.fromisoformat(date_string)
        # Format the datetime into a more readable format
        return dt.strftime("%m/%d/%Y, %I:%M %p")
    except ValueError:
        return "Invalid date format"


def format_providers(provider_data):
    formatted_providers = []
    for i, provider in enumerate(provider_data[:5], 1):
        properties = provider["properties"]
        first_name = properties.get("Provider First Name", "N/A")
        last_name = properties.get("Provider Last Name", "N/A")
        address = properties.get("Full Address", "N/A")
        phone = properties.get("Telephone Number", "N/A")
        formatted_providers.append(
            f"{i}. Name: {first_name} {last_name}, \nAddress: {address}, \nPhone: {phone} \n"
        )
    return "\n".join(formatted_providers)


def format_appointments(token, appointments):
    if not appointments:
        return "No appointments found."
    formatted_appointments = []
    for i, apt in enumerate(appointments[:10], 1):
        # formatted_date = format_datetime_readable(apt["start_datetime"])
        provider = search_provider(token, apt['provider_id'])

        provider_first_name = provider['properties']['Provider First Name']
        provider_last_name = provider['properties']['Provider Last Name']
        formatted_appointments.append(
            f"\n{i}. Provider: {provider_first_name} {provider_last_name}, \nDate: {apt["start_datetime"]}, \nReason: {apt.get('reason', 'N/A')}"
        )
    return "\n".join(formatted_appointments)


def format_schedule(availability):
    available_slots = [
        slot["start_datetime"] 
        for slot in availability 
        if not slot["is_booked"]
    ]
    
    if not available_slots:
        return "No available slots found."
    
    formatted_slots = [
        f"\n {i + 1}. {format_datetime_readable(slot)}"
        for i, slot in enumerate(available_slots[:7])
    ]
    return "Available times:\n" + "\n".join(formatted_slots)
@chatbot_bp.route("/", methods=["GET"])
def home():
    return "Chatbot is running!"
@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if user_message.lower() == "reset":
        user_context.clear()  # Allow user to reset the entire flow
        return jsonify({"message": "Conversation reset. Please start over by entering your email."})
    if not user_context.get("email"):
        user_context["email"] = user_message
        return jsonify({"message": "Please provide your password."})
    elif not user_context.get("password"):
        user_context["password"] = user_message
        # masked_password = "●" * len(user_message)  # Replace characters with black bubbles
        token = login(user_context["email"], user_context["password"])
        if not token:
            user_context.clear()
            return jsonify({"message": "Invalid email or password. Please try again."})
        user_context["token"] = token
        return jsonify({
            "message": f"Login successful! Do you want to cancel an appointment or book another one? (Type 'cancel' or 'book')"
        })
    elif user_message.lower() == "cancel" and not user_context.get("flow"):
        user_context["flow"] = "cancel"
        appointments = fetch_user_appointments(user_context["token"])
        if not appointments:
            user_context.clear()
            return jsonify({"message": "You have no appointments to cancel."})
        user_context["appointments"] = appointments
        formatted_appointments = format_appointments(user_context['token'], appointments)

        return jsonify({
            "message": f"Here are your appointments:\n{formatted_appointments}\n \nPlease choose one to cancel by its index (e.g. 1)."
        })
    elif user_context.get("flow") == "cancel" and not user_context.get("selected_appointment"):
        try:
            selected_index = int(user_message) - 1
            selected_appointment = user_context["appointments"][selected_index]
            success = cancel_user_appointment(
                user_context["token"], selected_appointment["id"]
            )
            if success:
                user_context.clear()
                return jsonify({"message": "Appointment successfully canceled."})
            else:
                user_context.clear()
                return jsonify({"message": "Failed to cancel the appointment. Try again later."})
        except (IndexError, ValueError):
            return jsonify({"message": "Invalid selection. Please try again."})
    elif not user_context.get("flow"):
        user_context["flow"] = "book"
        return jsonify({"message": "What symptoms are you experiencing?"})
    elif user_context.get("flow") == "book" and not user_context.get("specialty"):
        user_context["specialty"] = user_message
        return jsonify({"message": "Which insurance do you have?"})
    elif user_context.get("flow") == "book" and not user_context.get("insurance"):
        user_context["insurance"] = user_message
        return jsonify({"message": "Please provide your location (street, city, state, zip)."})
    elif user_context.get("flow") == "book" and not user_context.get("location"):
        user_context["location"] = user_message
        street, city, state, zip_code = user_message.split(", ")
        providers = search_providers(
            user_context["token"],
            user_context["specialty"],
            user_context["insurance"],
            street,
            city,
            state,
            zip_code,
        )
        if not providers:
            return jsonify({"message": "No providers found for your criteria. Try again with different inputs."})
        formatted_providers = format_providers(providers)
        user_context["providers"] = providers
        return jsonify({"message": f"Here are the top 5 providers:\n{formatted_providers}\nPlease choose one by its index (e.g. 1)."})
    elif user_context.get("flow") == "book" and not user_context.get("selected_provider"):
        try:
            selected_index = int(user_message) - 1
            user_context["selected_provider"] = user_context["providers"][selected_index]
            selected = user_context["selected_provider"]
            schedule = provider_sched(user_context["token"], selected["_id"])
            if schedule:
                availability = schedule.get("availability", [])
                formatted_schedule = format_schedule(availability)
                user_context["selected_schedule"] = availability
                return jsonify({
                    "message": f"Available times for {selected['properties']['Provider First Name']} {selected['properties']['Provider Last Name']}:\n{formatted_schedule}\nPlease choose one by its index (e.g. 1)."
                })
            else:
                return jsonify({
                    "message": f"Unfortunately, no schedule could be found for {selected['properties']['Provider First Name']} {selected['properties']['Provider Last Name']}."
                })
        except (IndexError, ValueError):
            user_context.clear()
            return jsonify({"message": "Invalid selection. Please try again."})
    elif user_context.get("flow") == "book" and not user_context.get("appointment_datetime"):
        try:
            selected_index = int(user_message) - 1
            availability = user_context["selected_schedule"]
            user_context["appointment_datetime"] = availability[selected_index]["start_datetime"]
            return jsonify({"message": "Please specify a reason for your appointment."})
        except (IndexError, ValueError):
            return jsonify({"message": "Invalid selection. Please try again."})
    elif user_context.get("flow") == "book" and not user_context.get("reason"):
        user_context["reason"] = user_message
        success = book_appointment(
            user_context["token"],
            user_context["selected_provider"]["_id"],
            user_context["selected_provider"]["properties"]["Provider First Name"],
            user_context["selected_provider"]["properties"]["Provider Last Name"],
            user_context["appointment_datetime"],
            user_context["reason"],
        )
        if success:
            ret = jsonify({"message": f"Your appointment with {selected['properties']['Provider First Name']} {selected['properties']['Provider Last Name']} is confirmedd"})
            user_context.clear()
            return ret
        else:
            user_context.clear()
            return jsonify({"message": "Failed to book the appointment. Try again later."})
    else:
        user_context.clear() 
        return jsonify({"message": "Thank you! Your process is complete."})