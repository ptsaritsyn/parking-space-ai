import json

from app.agents import _BaseAgent
from app.core.schemas import ReservationRequest
from pydantic import ValidationError

from app.db.models import User, Reservation, Spot
from app.llm.prompts import RESERVATION_EXTRACTION_PROMPT


class ChatAgent(_BaseAgent):
    def __init__(self, rag, guard, llm, sql_db):
        self.rag = rag
        self.guard = guard
        self.llm = llm
        self.sql_db = sql_db

    def _run(self, message):
        return self._handle_user_message(message)

    def _check_llm_response(self, llm_response):
        try:
            data = json.loads(llm_response)
            return data
        except Exception as e:
            raise Exception(f"LLM JSON Parse Error: {e}")

    def _handle_user_message(self, message: str) -> str:
        if "reserve" in message.lower():
            prompt = RESERVATION_EXTRACTION_PROMPT.format(message=message)
            llm_response = self.llm.generate(prompt)
            data = self._check_llm_response(llm_response)

            try:
                validated = ReservationRequest(**data)
            except ValidationError as e:
                example_message = (
                    "Please fill all necessary information for reservation using this example:"
                    "John Smith AA1234BB 2026-02-19T10:10:00 2026-02-19T10:11:00 reserve"
                )
                return example_message

            # Check free spots
            spot = self.sql_db.get(Spot, status="free")
            if not spot:
                return "Sorry, there are no available spots."

            # Check user
            user = self.sql_db.get(
                User,
                car_number=validated.car_number
            )
            if not user:
                user = self.sql_db.add(
                    User,
                    name=validated.name,
                    surname=validated.surname,
                    car_number=validated.car_number
                )
            else:
                return "Reservation with this car number already exist."

            # Create reservation
            reservation = self.sql_db.add(
                Reservation,
                user_id=user.id,
                spot_id=spot.id,
                reservation_from=validated.reservation_from,
                reservation_to=validated.reservation_to,
            )

            # Update spot status
            self.sql_db.update(
                Spot,
                {"id": spot.id},
                {"status": "reserved"}
            )

            reservation_info = (
                f"Reservation successful for {validated.name} {validated.surname}, car {validated.car_number}, "
                f"from {validated.reservation_from} to {validated.reservation_to} spot number {spot.number}."
            )
            return reservation_info
        else:
            response = self.rag.answer(message)
            safe_response = self.guard.filter(response)
            return safe_response
