from .on_command import on_command
from .on_command_error import on_command_error
from .on_ready import on_ready


def setup(client):
    client.add_cog(on_ready(client))
    client.add_cog(on_command_error(client))
    client.add_cog(on_command(client))
