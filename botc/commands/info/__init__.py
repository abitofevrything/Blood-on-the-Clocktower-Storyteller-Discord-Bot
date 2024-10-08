from .notes import Notes


def setup(client):
    client.add_cog(Notes(client))
