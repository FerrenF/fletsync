from config import ETSY_OPENAPI_URL
from util.openapi.openapi_interface import OpenAPI_Interface

interface = OpenAPI_Interface.from_remote_json(ETSY_OPENAPI_URL)
print(interface.command_dictionary.keys())
testcommand = interface.make_command("getMe")

print(testcommand)