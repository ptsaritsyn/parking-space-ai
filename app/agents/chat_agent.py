import json

import streamlit as st
from pydantic import ValidationError

from app.agents import _BaseAgent
from app.agents.admin_agent import AdminAgent
from app.core.schemas import ReservationRequest
from app.db.models import User, Reservation, Spot
from app.llm.prompts import RESERVATION_AGENT_EXTRACTION_PROMPT


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

    def render_waiting_block(self, reservation_data):
        st.markdown("##### Admin confirmation required")
        st.write(f"**User:** {reservation_data['name']} {reservation_data['surname']}")
        st.write(f"**Car number:** {reservation_data['car_number']}")
        st.write(f"**Reservation from:** {reservation_data['reservation_from']}")
        st.write(f"**Reservation to:** {reservation_data['reservation_to']}")
        st.write(f"**Spot number:** {reservation_data['spot_number']}")
        st.write(f"Waiting for administrator confirmation...")

    def _handle_user_message(self, message: str) -> str:
        if "reserve" in message.lower():
            prompt = RESERVATION_AGENT_EXTRACTION_PROMPT.format(message=message)
            llm_response = self.llm.generate(prompt)
            data = self._check_llm_response(llm_response)

            try:
                validated_data = ReservationRequest(**data)
            except ValidationError as e:
                example_message = (
                    "Please fill all necessary information for reservation using this example:"
                    "\n`John Smith AA1234BB 2026-04-19T10:10:00 2026-04-19T11:10:00 reserve`"
                )
                return example_message

            # Check free spots
            spot = self.sql_db.get(Spot, status="free")
            if not spot:
                return "Sorry, there are no available spots."

            reservation_data = {
                "name": validated_data.name,
                "surname":  validated_data.surname,
                "car_number": validated_data.car_number,
                "reservation_from": str(validated_data.reservation_from),
                "reservation_to": str(validated_data.reservation_to),
                "spot_number": spot.number
            }

            # Human-in-the-loop using LangChain AdminAgent
            admin_agent = AdminAgent()
            self.render_waiting_block(reservation_data)
            admin_response = admin_agent.run(json.dumps(reservation_data))

            if admin_response == "confirm":
                user = self._create_user(validated_data)
                if not user:
                    return "Reservation with this car number already exist."

                reservation = self._create_reservation(user, validated_data, spot)
                if not reservation:
                    return "Reservation error. Please clarify the reason via support@mail.com"

                spot = self._update_spot(spot)
                if not spot:
                    return "Reservation spot error. Please clarify the reason via support@mail.com"

                reservation_info = (
                    f"Reservation successful for {validated_data.name} {validated_data.surname}, " 
                    f"car {validated_data.car_number}, from {validated_data.reservation_from} "
                    f"to {validated_data.reservation_to} spot number {spot.number}."
                )
                return reservation_info

            else:
                return "Sorry, your reservation was refused by the administrator."

        else:
            response = self.rag.answer(message)
            safe_response = self.guard.filter(response)
            return safe_response

    def _create_user(self, data):
        user = self.sql_db.get(
            User,
            car_number=data.car_number
        )
        if not user:
            user = self.sql_db.add(
                User,
                name=data.name,
                surname=data.surname,
                car_number=data.car_number
            )

            return user
        return None

    def _create_reservation(self, user, data, spot):
        reservation = self.sql_db.add(
            Reservation,
            user_id=user.id,
            spot_id=spot.id,
            reservation_from=data.reservation_from,
            reservation_to=data.reservation_to,
        )

        if reservation:
            return reservation
        return None

    def _update_spot(self, spot):
        spot = self.sql_db.update(
            Spot,
            {"id": spot.id},
            {"status": "reserved"}
        )

        if spot:
            return spot
        return None
