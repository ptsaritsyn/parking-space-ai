from typing import Literal
import json

from langgraph.graph import StateGraph, START, END

from app.agents.admin_agent import AdminAgent
from app.core.schemas import ReservationRequest
from app.llm.prompts import RESERVATION_AGENT_EXTRACTION_PROMPT
from app.orchestration import _BaseGraph
from app.orchestration.state import State


class ReservationGraph(_BaseGraph):
    def __init__(self, agent):
        self.agent = agent
        self.graph = self.build()

    def start_node(self, state: State) -> State:
        return state

    def start_decide_node(self, state: State) -> Literal["rag_node", "reservation_node"]:
        message = state["graph_state"].get("message", "")
        if "reserve" in message.lower():
            return "reservation_node"
        return "rag_node"

    def rag_node(self, state: State) -> State:
        message = state["graph_state"].get("message", "")
        response = self.agent.rag.answer(message)
        safe_response = self.agent.guard.filter(response)

        state = state.copy()
        state["graph_state"] = state["graph_state"].copy()
        state["graph_state"]["response"] = safe_response

        return state

    def reservation_node(self, state: State) -> State:
        message = state["graph_state"].get("message", "")
        prompt = RESERVATION_AGENT_EXTRACTION_PROMPT.format(message=message)
        llm_response = self.agent.llm.generate(prompt)
        try:
            data = self.agent._check_llm_response(llm_response)
            validated_data = ReservationRequest(**data)
        except Exception:
            state = state.copy()
            state["graph_state"] = state["graph_state"].copy()
            state["graph_state"]["error"] = (
                "Please fill all necessary information for reservation using this example:\n"
                "`John Smith AA1234BB 2026-04-19T10:10:00 2026-04-19T11:10:00 reserve`"
            )
            return state

        spot = self.agent._get_spot(status="free")
        if not spot:
            state = state.copy()
            state["graph_state"] = state["graph_state"].copy()
            state["graph_state"]["response"] = "Sorry, there are no available spots."
            return state

        reservation_data = {
            "name": validated_data.name,
            "surname": validated_data.surname,
            "car_number": validated_data.car_number,
            "reservation_from": str(validated_data.reservation_from),
            "reservation_to": str(validated_data.reservation_to),
            "spot_number": spot.number,
            "token": self.agent.mcp_access_token
        }

        self.agent.render_waiting_block(reservation_data)

        admin_agent = AdminAgent()
        admin_response = admin_agent.run(json.dumps(reservation_data))

        state = state.copy()
        state["graph_state"] = state["graph_state"].copy()
        state["graph_state"]["validated_data"] = validated_data
        state["graph_state"]["spot"] = spot
        state["graph_state"]["reservation_data"] = reservation_data
        state["graph_state"]["admin_response"] = admin_response
        return state

    def admin_confirmation_node(self, state: State) -> Literal["refuse_node", "create_node"]:
        if state["graph_state"].get("admin_response") == "confirm":
            return "create_node"
        return "refuse_node"

    def refuse_node(self, state: State) -> State:
        state = state.copy()
        state["graph_state"] = state["graph_state"].copy()

        if state["graph_state"].get("error"):
            state["graph_state"]["response"] = state["graph_state"].get("error")
        else:
            state["graph_state"]["response"] = "Sorry, your reservation was refused by the administrator."

        return state

    def create_node(self, state: State) -> State:
        graph_state = state["graph_state"]
        validated_data = graph_state["validated_data"]
        spot = graph_state["spot"]
        reservation_data = graph_state["reservation_data"]

        user = self.agent._create_user(validated_data)
        if not user:
            state = state.copy()
            state["graph_state"] = state["graph_state"].copy()
            state["graph_state"]["response"] = "Reservation with this car number already exist."
            return state

        reservation = self.agent._create_reservation(user, validated_data, spot)
        if not reservation:
            state = state.copy()
            state["graph_state"] = state["graph_state"].copy()
            state["graph_state"]["response"] = "Reservation error. Please clarify the reason via support@mail.com"
            return state

        spot = self.agent._update_spot(spot)
        if not spot:
            state = state.copy()
            state["graph_state"] = state["graph_state"].copy()
            state["graph_state"]["response"] = "Reservation spot error. Please clarify the reason via support@mail.com"
            return state

        self.agent.mcp_client.call_tool("write_reservation_to_file", **reservation_data)
        reservation_info = (
            f"Reservation successful for {validated_data.name} {validated_data.surname}, "
            f"car {validated_data.car_number}, from {validated_data.reservation_from} "
            f"to {validated_data.reservation_to} spot number {spot.number}."
        )
        state = state.copy()
        state["graph_state"] = state["graph_state"].copy()
        state["graph_state"]["response"] = reservation_info
        return state

    def _build(self):
        builder = StateGraph(State)
        builder.add_node("start_node", self.start_node)
        builder.add_node("rag_node", self.rag_node)
        builder.add_node("reservation_node", self.reservation_node)
        builder.add_node("refuse_node", self.refuse_node)
        builder.add_node("create_node", self.create_node)

        builder.add_edge(START, "start_node")
        builder.add_conditional_edges("start_node", self.start_decide_node)
        builder.add_edge("rag_node", END)
        builder.add_conditional_edges("reservation_node", self.admin_confirmation_node)
        builder.add_edge("refuse_node", END)
        builder.add_edge("create_node", END)

        return builder.compile()

    def _invoke(self, state: State) -> State:
        return self.graph.invoke(state)
