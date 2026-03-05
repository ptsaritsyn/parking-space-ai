import json
import os

import streamlit as st

from app.agents import _BaseAgent
from app.db.models import User, Reservation, Spot
from app.orchestration.graph import ReservationGraph
from app.orchestration.state import State
from app.service.mcp_client import MCPClientWrapper, MCPAsyncStdioClient


class ChatAgent(_BaseAgent):
    def __init__(self, rag, guard, llm, sql_db):
        self.rag = rag
        self.guard = guard
        self.llm = llm
        self.sql_db = sql_db
        self.mcp_access_token = os.getenv("MCP_ACCESS_TOKEN")
        self.mcp_client = MCPClientWrapper(MCPAsyncStdioClient)
        self.mcp_client.connect()
        self.graph = ReservationGraph(self)

    def _run(self, message):
        state: State = {
            "graph_state": {"message": message}
        }
        result = self.graph.invoke(state)
        return result["graph_state"].get("response", "")

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

    def _get_spot(self, status):
        spot = self.sql_db.get(Spot, status=status)

        if spot:
            return spot
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
