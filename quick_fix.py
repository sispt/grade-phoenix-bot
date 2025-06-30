# quick_fix.py

# Define the response dictionary first (trimmed down version here for clarity)
response = {
    "data": {
        "getPage": {
            "panels": [
                {
                    "blocks": [
                        {
                            "name": "block_0",
                            "type": "simple",
                            # ...
                        },
                        {
                            "name": "testpage_track_10459",
                            "type": "simple",
                            # ...
                        }
                    ]
                }
            ]
        }
    },
    "status": True
}

# Now you can safely access the blocks
blocks = response["data"]["getPage"]["panels"][0]["blocks"]
print(blocks)
