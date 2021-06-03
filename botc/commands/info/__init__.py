from .claim import Claim
from .notes import Notes
from .info import Info

def setup(client):
    client.add_cog(Notes(client))

    # Must load info and claim cog after notes cog as it
    # depends on the notes cog being loaded for getting 
    # the callback
    client.add_cog(Info(client))
    client.add_cog(Claim(client))
