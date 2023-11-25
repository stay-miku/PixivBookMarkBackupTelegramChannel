

isLock = False


def lock():
    global isLock
    isLock = True


def unlock():
    global isLock
    isLock = False
