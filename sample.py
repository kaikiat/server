import serial
import time
import threading
import imagezmq
import socket
from picamera2 import Picamera2, Preview
from libcamera import Transform

# Open both Serial ports of Tablet and STM32
try:
    TABLET_SER = serial.Serial('/dev/rfcomm0', baudrate=9600, timeout=1)
except serial.SerialException:
    print("Please connect the android tablet to RPi")
    exit(0)
try:
    STM_SER = serial.Serial('/dev/ttyUSB0', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
except serial.SerialException:
    print("Please connect the RPi to the STM")
    exit(0)

# STATIC VARS
STM_COMPLETED_STRING = "COMPLE"
STM_BUFFER_SIZE = 16
TURN_LIST = ["q", "e", "z", "c"]
SECOND_CHAR_LIST = ["w", "q", "e", "z", "c", "x", "s"]
DIRECTIONS = ["N", "S", "E", "W"]
VALID_INSTR = "IS_VALID_INSTR"
VALID_POSITION = "IS_VALID_POSITION"

# GLOBAL DYNAMICS -- INSTR, STM, ALGO
INSTRUCTION_COUNT = 0
INSTRUCTIONS = []  # instructions on hold to be transferred to STM\

STM_COUNT = 1
STM_QUEUE = [0]  # instructions already transferred to STM but not executed yet

POSITIONS_FOR_ALGO = []
TEMP_INSTR_STRING = []
POSITION_ALGO_COUNT = 0
OBSTACLE_ORDER = []
# INST_COUNT_BY_ALGO = -1
INST_COUNT_BY_ALGO = 0

# LOCKS
INSTRUCTIONS_LOCK = threading.Lock()
STM_LOCK = threading.Lock()
ALGO_COORD_LOCK = threading.Lock()

# CV ADDRESSING CONFIGURATION
ADDRESS = 'tcp://192.168.1.21:5555'  # Receiver address, use ifconfig to check
HOST = socket.gethostname()
DELAY = 2

sender = imagezmq.ImageSender(connect_to=ADDRESS)

# Configure picam
picam2 = Picamera2()
config = picam2.create_still_configuration(
    transform=Transform(hflip=True, vflip=True))
picam2.configure(config)
picam2.start()


# CV CAM FUNCTION
def capture_and_send():
    try:
        print('Preparing to take photo')
        nparray = picam2.capture_array()
        response = sender.send_image(HOST, nparray)
        return response
    except Exception as e:
        print(e)


# Generic send functions
def encode_to_tablet(message):
    TABLET_SER.write(message.encode())


def encode_to_stm(message):
    time.sleep(0.05)
    STM_SER.write(message.encode())
    print(f"Attempted to add to STM:{message}")
    print(f"{message.encode()}")


def forward_to_tablet(message):
    TABLET_SER.write(message)


def forward_stm(message):
    time.sleep(0.5)
    STM_SER.write(message)
    print(f"Attempted to add to STM:{message}")
    print(f"{message}")


# ====== TABLET SIDE OF CODE ======
def process_tablet_data(data):
    """ Makes 'ns000nw020' to '["ns000","nw020"]', formulating to list """
    preprocessed_data = data.split("n")
    preprocessed_data = ["n" + value for value in preprocessed_data]
    if data[0] != "n":
        preprocessed_data[0] = preprocessed_data[0][1:]
    else:
        preprocessed_data.pop(0)
    processed_data = [instr_or_pos.strip() for instr_or_pos in preprocessed_data]
    return processed_data


def is_valid_instruction_or_position(instruction):
    """ This function checks for validity of an instruction returns false if invalid, returns true if valid """
    try:
        if len(instruction) == 5 and instruction[0] == "n" and instruction[
            1].lower() in SECOND_CHAR_LIST and instruction[2:].isdigit():
            return VALID_INSTR
        elif len(instruction) == 7 and instruction[0] == "n" and int(instruction[1:3]) in range(1, 21) and int(instruction[3:5]) in range(1, 21) and \
                int(instruction[5]) in range(1, 10) and instruction[6].upper() in DIRECTIONS:
            return VALID_POSITION
        else:
            return False
    except AttributeError:
        print(f"'{instruction}' is invalid.")
        return False


def sort_to_position_or_instructions(processed_list):
    global POSITIONS_FOR_ALGO, INSTRUCTION_COUNT, INSTRUCTIONS
    instruction_position = 0
    removal_queue = []
    algo_queue = []

    for item in processed_list:
        if is_valid_instruction_or_position(item) == VALID_INSTR:
            pass
        elif is_valid_instruction_or_position(item) == VALID_POSITION:
            algo_queue.append(instruction_position)
            removal_queue.append(instruction_position)
        else:
            removal_queue.append(instruction_position)
        instruction_position += 1
    algo_queue.reverse()
    INSTRUCTIONS_LOCK.acquire()
    ALGO_COORD_LOCK.acquire()
    for position in algo_queue:
        print(f"New algo position:{processed_list[position]}")
        POSITIONS_FOR_ALGO.append(processed_list[position])
    print(f"Positions gathered:{POSITIONS_FOR_ALGO}")
    ALGO_COORD_LOCK.release()
    removal_queue.reverse()
    for each in removal_queue:  # loop through position of invalid instructions
        processed_list.pop(each)  # exile invalid instructions
    if len(processed_list) > 0:  # if more than one new instruction
        INSTRUCTION_COUNT += len(processed_list)  # update with remaining valid instructions if any
        INSTRUCTIONS.extend(processed_list)  # update with remaining valid instructions if any
        print(f"{INSTRUCTION_COUNT} new instruction(s)")
    else:
        pass
    INSTRUCTIONS_LOCK.release()


# ====== STM SIDE OF CODE ======
def update_stm_queue(stm_data):
    """ This function interprets data from STM and clear completed STM instructions from queue """
    global STM_COUNT, STM_QUEUE, INST_COUNT_BY_ALGO
    queued_to_clear = stm_data.upper().count(STM_COMPLETED_STRING)
    print(f"{queued_to_clear} item(s) to delete from Queue")
    STM_LOCK.acquire()  # LOCK STM
    ALGO_COORD_LOCK.acquire()
    STM_COUNT -= queued_to_clear
    INST_COUNT_BY_ALGO -= queued_to_clear
    ALGO_COORD_LOCK.release()
    for queue_position in range(queued_to_clear):
        STM_QUEUE.pop(0)
    if queued_to_clear > 0:
        print(f"{queued_to_clear} just cleared from queue. {STM_COUNT} instructions left in queue...")
        print(f"Algo count: {INST_COUNT_BY_ALGO}")
    STM_LOCK.release()  # UNLOCK STM


def add_stm_queue(limit):
    """ This functions adds as much instructions into STM queue as possible """
    global STM_COUNT, STM_QUEUE
    STM_LOCK.acquire()  # LOCK STM
    INSTRUCTIONS_LOCK.acquire()  # LOCK INSTRUCTIONS
    if limit >= INSTRUCTION_COUNT:
        for position in range(INSTRUCTION_COUNT):
            encode_to_stm(INSTRUCTIONS[position])
            encode_to_tablet(INSTRUCTIONS[position])  # ADDED THIS TO GIVE ANDROID CODE
            STM_QUEUE.extend(INSTRUCTIONS[position])
        print(f"{INSTRUCTION_COUNT} instruction(s) added into queue.")
        STM_COUNT += INSTRUCTION_COUNT
        INSTRUCTIONS_LOCK.release()  # UNLOCK INSTRUCTIONS
        STM_LOCK.release()  # UNLOCK STM
        update_instructions(INSTRUCTION_COUNT)
    else:
        for position in range(limit):
            encode_to_stm(INSTRUCTIONS[position])
            encode_to_tablet(INSTRUCTIONS[position])  # ADDED THIS TO GIVE ANDROID CODE
            STM_QUEUE.extend(INSTRUCTIONS[position])
        print(f"{limit} instruction(s) added into queue.")
        STM_COUNT += limit
        INSTRUCTIONS_LOCK.release()  # UNLOCK INSTRUCTIONS
        STM_LOCK.release()  # UNLOCK STM
        update_instructions(limit)


def update_instructions(count_to_clear):
    """ This function removes first instruction(s) from INSTRUCTIONS upon added onto STM_QUEUE. """
    global INSTRUCTIONS, INSTRUCTION_COUNT
    INSTRUCTION_COUNT -= count_to_clear
    for position in range(count_to_clear):
        del INSTRUCTIONS[0]
    print(f"{INSTRUCTION_COUNT} pending instruction(s) left to add to queue.")


# ====== ALGO SIDE OF CODE ======
def process_algo_list():
    """ use received Algo instructions, run it through till image """
    global INSTRUCTIONS, INSTRUCTION_COUNT, TEMP_INSTR_STRING, INST_COUNT_BY_ALGO
    ALGO_COORD_LOCK.acquire()
    INSTRUCTIONS_LOCK.acquire()
    print(f"algo queue: {TEMP_INSTR_STRING}")
    send_to_STM = TEMP_INSTR_STRING[0]
    print(f"Processing: {send_to_STM}")
    instr = send_to_STM.split(",")
    TEMP_INSTR_STRING.remove(send_to_STM)
    # counter = 0
    for each in instr:
        INSTRUCTIONS.append(each)
        INSTRUCTION_COUNT += 1
        INST_COUNT_BY_ALGO += 1
    INSTRUCTIONS_LOCK.release()
    ALGO_COORD_LOCK.release()


def get_algo_instructions():
    """ Give algo positions, get from algo order+instructions """
    global POSITIONS_FOR_ALGO, TEMP_INSTR_STRING, POSITION_ALGO_COUNT, OBSTACLE_ORDER, INST_COUNT_BY_ALGO
    ip = "192.168.1.21"
    port = 6969
    s = socket.socket()
    ALGO_COORD_LOCK.acquire()
    POSITION_ALGO_COUNT = len(POSITIONS_FOR_ALGO)
    print(f"before sending:{POSITIONS_FOR_ALGO}")
    message = ",".join(POSITIONS_FOR_ALGO)
    print(f"Sending this information to ALGO: {message}")
    s.connect((ip, port))
    s.send(message.encode())
    print("waiting for response")
    message = s.recv(1024).decode()
    print(f"Received this from algo:{message}")
    if ":" in message:
        # yo. legit. fuck this. This thing finds the order of the ID processed then extracts it and removes it from instructions
        # message = "3, 1, 2, ns000, nq010:nz010, ns000" -> TEMP_INSTR_STRING = ["ns000,nq010","nz010,ns000"] OBSTACLE_ORDER = [3,1,2]
        TEMP_INSTR_STRING = message.split(":")  # algo? formatting how?
        temp_obst_ord_str = TEMP_INSTR_STRING[0]
        temp_obst_ord = temp_obst_ord_str.split(",")  # ALGO PLS CHECK!!!! NOT SURE FORMATTING HAS SPACE OR NOT at this point IDK
        OBSTACLE_ORDER = [eval(obstacle) for obstacle in temp_obst_ord[:POSITION_ALGO_COUNT]]
        for each in range(POSITION_ALGO_COUNT):
            temp_obst_ord.pop(0)
        first = ",".join(temp_obst_ord)
        TEMP_INSTR_STRING.pop(0)
        TEMP_INSTR_STRING.insert(0, first)
    else:
        # "1, 3, 2, ns100,nq010" -> [1,3,2] ["ns100,nq010"]
        temp_obst_ord = message
        temp_obst_ord = temp_obst_ord.split(",")  # ALGO PLS CHECK!!!! NOT SURE FORMATTING HAS SPACE OR NOT
        OBSTACLE_ORDER = [eval(obstacle) for obstacle in temp_obst_ord[:POSITION_ALGO_COUNT]]
        for each in range(POSITION_ALGO_COUNT):
            temp_obst_ord.pop(0)
        first = ",".join(temp_obst_ord)
        TEMP_INSTR_STRING.append(first)
    POSITIONS_FOR_ALGO = []
    ALGO_COORD_LOCK.release()
    s.close()


# ====== WHERE SHIT(multithreading) HAPPENS T1 to T5 ======
def check_tablet_data():  # T1
    """ When tablet data is received by Pi I feel sad """
    print("T1         Tablet...")
    while True:
        tablet_data = TABLET_SER.readline().decode().strip()
        if tablet_data:
            processed = process_tablet_data(tablet_data)
            sort_to_position_or_instructions(processed)
            encode_to_tablet(f"{INSTRUCTION_COUNT} instructions pending...")
            encode_to_tablet(f"{STM_COUNT} instructions in queue...")
            encode_to_tablet(f"{len(POSITIONS_FOR_ALGO)} positions to send...")
        else:
            pass  # change this if you want Pi to send something to tablet


def check_for_stm_data():
    print("  T2       STM...")
    while True:
        stm_data = STM_SER.readline().decode().strip()
        if stm_data:
            print(f"received {stm_data}")
            update_stm_queue(stm_data)  # update RPI knowledge of queue on STM if any updates
        if STM_COUNT < STM_BUFFER_SIZE:  # try to update queue if space exists
            if INSTRUCTION_COUNT > 0:  # check if there are any instructions to add
                limit = STM_BUFFER_SIZE - STM_COUNT  # limit of max items that can be added to queue
                add_stm_queue(limit)  # add instructions to limit


def check_instructions_from_algo():
    print("    T3     Algo (Send positions to algo)")
    while True:
        time.sleep(0.45)
        if len(POSITIONS_FOR_ALGO) > 0:
            print("entered T3")
            get_algo_instructions()
            process_algo_list()


def check_coords_for_algo():
    print("      T4   Algo (Update new algo capture)")
    while True:
        time.sleep(0.5)
        if len(TEMP_INSTR_STRING) > 0 and INST_COUNT_BY_ALGO == -1:
            process_algo_list()


def check_if_algo_instr_completed():
    print("        T5 complete and snap")
    while True:
        global INST_COUNT_BY_ALGO, OBSTACLE_ORDER
        time.sleep(0.6)
        ALGO_COORD_LOCK.acquire()
        print('T5 INST_COUNT_BY_ALGO  =',INST_COUNT_BY_ALGO)
        if INST_COUNT_BY_ALGO == 0 and OBSTACLE_ORDER:
            INST_COUNT_BY_ALGO -= 1
            print("Running T5")
            byte_response = capture_and_send()
            response = int(byte_response.decode())
            print(f"Response : {response}")
            # encode_to_tablet(f"TARGET-{OBSTACLE_ORDER[0]}-5")
            encode_to_tablet(f"TARGET-{OBSTACLE_ORDER[0]}-{response}")
            OBSTACLE_ORDER.pop(0)
        ALGO_COORD_LOCK.release()


def main():
    global INST_COUNT_BY_ALGO
    print("Running dummy")
    encode_to_stm("ns000")
    print("\n\n==========.=======================\nT1T2T3T4T5")
    t1 = threading.Thread(target=check_tablet_data, name='t1')
    t2 = threading.Thread(target=check_for_stm_data, name='t2')
    t3 = threading.Thread(target=check_coords_for_algo, name='t3')
    t4 = threading.Thread(target=check_instructions_from_algo, name='t4')
    t5 = threading.Thread(target=check_if_algo_instr_completed, name='t5')
    time.sleep(2)
    ALGO_COORD_LOCK.acquire()
    INST_COUNT_BY_ALGO +=1
    print(f"Total instr left{INST_COUNT_BY_ALGO}")
    ALGO_COORD_LOCK.release()
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()


if __name__ == '__main__':
   main()  # yeet.
#    while True:
#    	capture_and_send()