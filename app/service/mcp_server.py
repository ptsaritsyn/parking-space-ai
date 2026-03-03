import os
from datetime import datetime
from dotenv import load_dotenv
from functools import wraps

from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(
    name="ReservationStorage"
)


def check_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = kwargs.get("token", None)
        mcp_access_token = os.getenv("MCP_ACCESS_TOKEN")

        if mcp_access_token is None or token != mcp_access_token:
            return "Unauthorized access, please set MCP_ACCESS_TOKEN to environment"

        kwargs.pop("token", None)
        return func(*args, **kwargs)
    return wrapper


@mcp.tool()
@check_auth
def write_reservation_to_file(
        name: str,
        car_number: str,
        reservation_from: str,
        reservation_to: str,
        spot_number: str,
        token: str = ""
) -> str:

    """
    Writes parking reservation details to storage after administrator confirmation.
    Params:
        name (str): Full name of the person making the reservation.
        car_number (str): Car license plate number.
        reservation_from (str): Start datetime of the reservation (ISO format).
        reservation_to (str): End datetime of the reservation (ISO format).
        spot_number (str): Number of the reserved parking spot.

    Returns:
        str: Success message or error description.
    """

    approval_time = datetime.now().isoformat()
    header = "Name | Car Number | Reservation Period | Spot Number | Approval Time\n"
    line = f"{name} | {car_number} | {reservation_from} - {reservation_to} | {spot_number} | {approval_time}\n"
    storage = "reservations.txt"
    try:
        write_header = not os.path.exists(storage) or os.path.getsize(storage) == 0
        with open(storage, "a") as f:
            if write_header:
                f.write(header)
            f.write(line)
        return f"Reservation written successfully to {storage}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
