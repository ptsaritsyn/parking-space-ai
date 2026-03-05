import json
import os

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from . import _BaseAgent
from app.llm.prompts import CONFIRMATION_AGENT_SYSTEM_PROMPT


class AdminAgent(_BaseAgent):

    @tool
    @staticmethod
    def admin_confirmation(input_str: str) -> str:
        """
        Confirms the reservation request.
        """

        print(json.dumps(json.loads(input_str), indent=4, ensure_ascii=False))
        result = input("Confirm reservation with data above: ")

        if result.strip() == "confirm":
            return "confirm"
        else:
            return "refuse"

    def _run(self, reservation_data: str) -> str:
        model = ChatOpenAI(model="gpt-3.5-turbo", api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
        tools = [self.admin_confirmation]
        agent = create_agent(
            model,
            tools=tools,
            system_prompt=CONFIRMATION_AGENT_SYSTEM_PROMPT
        )

        response = agent.invoke({
            "messages": [
                HumanMessage(
                    f"Confirm this reservation request with these reservation data: {reservation_data}"
                )
            ]
        })

        return response["messages"][-1].content
