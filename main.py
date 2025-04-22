from multiprocessing import Manager, Process
from nodes.schedule_manager import main as schedule_manager_main
from nodes.machine_handler import main as machine_handler_main

def schedule_manager(shared_state):
    """
    Wrapper for the schedule_manager main function.
    Passes the shared state to the schedule_manager.
    """
    schedule_manager_main(shared_state)

def machine_handler(shared_state):
    """
    Wrapper for the machine_handler main function.
    Passes the shared state to the machine_handler.
    """
    machine_handler_main(shared_state)

if __name__ == "__main__":
    with Manager() as manager:
        # Initialize the shared state
        shared_state = manager.dict()
        shared_state['session_proposals'] = manager.list()
        shared_state['current_schedule'] = manager.dict()

        # Start the schedule_manager and machine_handler processes
        p1 = Process(target=schedule_manager, args=(shared_state,))
        p2 = Process(target=machine_handler, args=(shared_state,))
        p1.start()
        p2.start()
        p1.join()
        p2.join()
