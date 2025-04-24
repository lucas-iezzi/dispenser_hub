import asyncio
from multiprocessing import Manager, Process, Event
from nodes.schedule_manager import main as schedule_manager_main
from nodes.machine_handler import main as machine_handler_main

def main():
    # Create a shared state using Manager
    with Manager() as manager:
        shared_state = manager.dict()

        # Create an event to synchronize the processes
        schedule_manager_ready = Event()

        # Create a single event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Start the schedule_manager process
        schedule_manager_process = Process(
            target=schedule_manager_main, 
            args=(shared_state, loop, schedule_manager_ready)
        )
        schedule_manager_process.start()

        # Start the machine_handler process (waits for schedule_manager_ready)
        machine_handler_process = Process(
            target=machine_handler_main, 
            args=(shared_state, loop, schedule_manager_ready)
        )
        machine_handler_process.start()

        # Run the event loop
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            schedule_manager_process.terminate()
            machine_handler_process.terminate()

if __name__ == "__main__":
    main()
