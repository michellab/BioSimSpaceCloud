import fdk
import json

def handler(ctx, data=None, loop=None):
    name = "World"
    if data and len(data) > 0:
        body = json.loads(data)
        name = body.get("name")
    return {"message": "Hello {0} from Gromacs on Fn".format(name)}

if __name__ == "__main__":
    fdk.handle(handler)
