import asyncio
from dcs_link import DCSLink, LinkConfig

bios = insight = None

def on_pilotname(value):
    """Handle change events."""
    print(f"Pilot name is: {value}")
    # Remove event handler
    bios.off("PILOTNAME")

async def main():
    global bios, insight

    config = LinkConfig()
    bios, insight = DCSLink(config)

    # Connect to DCS-BIOS and DCS-Insight
    if await bios.connect() and await insight.connect():

        print(bios.aircraft_name)
        print(bios.events)
        print(insight.apis)

        # Open the rear flap, no return value
        await insight.call("LoSetCommand(iCommand)", iCommand=145)
        # Get mission start time, return string
        print(await insight.call("LoGetMissionStartTime()", timeout = 10))
        
        # Register event handlers
        bios.on("PILOTNAME", on_pilotname)
        bios.on("FC3_ANGLE_OF_ATTACK", lambda value: print(f"Attack changed to: {value}"))
        # Clean up resources, bios.close() is called automatically.
        bios.on("MISSION_ENDED", lambda _: insight.close())
        
        # Keep running to listen for events
        while True:
            await asyncio.sleep(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
        bios.close()
        insight.close()