from multiprocessing import Process, Semaphore, Value, Array, current_process, Lock, Manager

#global variable
CRATE_MAX = 12  
MAX_FRUIT = 1500

def person_picker(crate, crate_ind, tree_ind, tree, crate_full, crate_mutex, pickers_completed, done_mutex, turns):
    picker_id = int(current_process().name.split('-')[1]) - 1

    while True:  
        fruit = None
        with done_mutex:
            if tree_ind.value >= len(tree) :
                break
        turns[picker_id].acquire()

        with crate_mutex:           # Check if crate has space
            if crate_ind.value < CRATE_MAX:
                
                # Check if all fruits are picked
                with done_mutex:  
                    if tree_ind.value < len(tree):
                        fruit_index = tree_ind.value
                        fruit = tree[fruit_index]
                        tree_ind.value += 1

                if fruit is not None:
                    crate[crate_ind.value] = fruit
                    # Change here: showing 1-based index for crate slot
                    print(f"{current_process().name} grabbed fruit {fruit} and tossed it into crate slot [{crate_ind.value + 1}/{CRATE_MAX}]")
                    crate_ind.value += 1

                    if crate_ind.value == CRATE_MAX:
                        print(f"{current_process().name} filled the crate. Notifying the loader...")
                        print(f"Crate contents: {list(crate[:CRATE_MAX])}\n")
                        crate_full.release()

        next_picker = (picker_id + 1) % 3
        turns[next_picker].release()

    with done_mutex:    # Handle process termination
        pickers_completed.value += 1
        print(f"{current_process().name} finished. {pickers_completed.value}/3 pickers done.")
        if pickers_completed.value == 3:
            crate_full.release()
    next_picker = (picker_id + 1) % 3
    turns[next_picker].release()


def person_loader(crate, crate_ind, crate_full, pickers_completed, crate_mutex):
    crate_count = 0
    while True:
        crate_full.acquire()
        with crate_mutex:
            if crate_ind.value > 0:
                crate_count += 1
                print(f"[Loader] Loading crate {crate_count} in truck: {list(crate[:crate_ind.value])} ({crate_ind.value} fruits)\n")
                crate_ind.value = 0

            if pickers_completed.value == 3 and crate_ind.value == 0:    # Exit condition
                print("[Loader] All crates loaded in truck . Loader exiting.")
                break


def run_simulation(num_fruits):
    print(f"\n--- Running simulation with {num_fruits} fruits ---")
    manager = Manager()
    tree = manager.list([i + 1 for i in range(num_fruits)])     # Shared fruit tree   (Known globally)

    crate = Array('i', CRATE_MAX)            # Shared crate array
    crate_ind = Value('i', 0)
    tree_ind = Value('i', 0)
    crate_full = Semaphore(0)           # Signals when crate is full
    pickers_completed = Value('i', 0)
    crate_mutex = Lock()                # Protects crate access
    done_mutex = Lock()
    turns = [Semaphore(0) for _ in range(3)]        # Semaphores for each picker
    turns[0].release()

    pickers = [
        Process(
            target=person_picker,
            name=f"Picker-{i+1}",
            args=(crate, crate_ind, tree_ind, tree, crate_full,crate_mutex , pickers_completed, done_mutex, turns)
        )
        for i in range(3)
    ]

    loader_proc = Process(
        target=person_loader,
        args=(crate, crate_ind, crate_full, pickers_completed, crate_mutex)
    )

    for p in pickers:
        p.start()
    loader_proc.start()

    for p in pickers:
        p.join()
    loader_proc.join()
    print(f"--- Simulation complete for {num_fruits} fruits ---\n")

def main():
    print("\n" + "="*50)
    print(" SPRING WORKERS SIMULATION – FRUIT PICKING SYSTEM ")
    print("="*50 + "\n")
    
    print("Choose mode:")
    print("1. Enter number of fruits")
    print("2. Run test cases")
    choice = input("Enter 1 or 2: ").strip()

    if choice == '1':
        try:
            num_fruits = int(input("Enter number of fruits on the tree: "))
            if num_fruits <= 0:
                print("Please enter a positive integer.")
                return
            elif num_fruits > MAX_FRUIT:
                print(f"Please enter between 1 and {MAX_FRUIT}") 
                return
            run_simulation(num_fruits)
        except ValueError:
            print("Invalid input.")
    elif choice == '2':
        test_cases = [0, 6, 12, 18, 1501]  # Added test cases including edge cases
        for tc in test_cases:
            if tc <= 0:
                print(f"\nYou enter number {tc}: Please enter positive number")
            elif tc > MAX_FRUIT:
                print(f"\nYou enter number {tc}: Please enter between 1 and {MAX_FRUIT} fruits")
            else:
                print(f"\nRunning test case with {tc} fruits:")
                run_simulation(tc)
    else:
        print("Invalid choice.\nExiting.")

if __name__ == "__main__":
    main()