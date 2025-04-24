import asyncio
from multiprocessing import Manager, Process
from nodes.schedule_manager import main as schedule_manager
from nodes.machine_handler import main as machine_handler

if __name__ == "__main__":
    with Manager() as manager:

        # Initialize the shared state
        shared_state = manager.dict()
        shared_state['session_proposals'] = manager.list()
        shared_state['current_schedule'] = manager.dict()

        # Create a single event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Start the schedule_manager and machine_handler processes
        schedule_manager_process = Process(target=schedule_manager, args=(shared_state, loop))
        machine_handler_process = Process(target=machine_handler, args=(shared_state, loop))

        schedule_manager_process.start()
        machine_handler_process.start()

        # Run the event loop
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            schedule_manager_process.terminate()
            machine_handler_process.terminate()
