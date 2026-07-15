with open("cowsignal.in") as read:
    height, width, scale = map(int, read.readline().split())
    signal = [read.readline() for _ in range (height)]
with open("cowsignal.out", "w") as written:
    for i in range (height * scale):
        for j in range (width * scale):
            print(signal[i//scale][j//scale], end="", file=written)
        print(file=written)
