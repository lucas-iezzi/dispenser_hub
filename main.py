from multiprocessing import Manager, Process, Event
from nodes.schedule_manager import main as schedule_manager_main
from nodes.machine_handler import main as machine_handler_main

def main():
    with Manager() as manager:
        # Create a Manager to handle shared state
        shared_state = manager.dict()
        shared_state_flag = Event()
        schedule_manager_ready = Event()

        # Start schedule_manager process
        schedule_manager_process = Process(
            target=schedule_manager_main,
            args=(shared_state, shared_state_flag, schedule_manager_ready)
        )
        schedule_manager_process.start()

        # Start machine_handler process
        machine_handler_process = Process(
            target=machine_handler_main,
            args=(shared_state, shared_state_flag, schedule_manager_ready)
        )
        machine_handler_process.start()

        try:
            schedule_manager_process.join()
            machine_handler_process.join()
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            # Shut down the system cleanly
            schedule_manager_process.terminate()
            machine_handler_process.terminate()