bucket_count = 3
turn_count = 100
capacity = [0 for _ in range (bucket_count)]
milk = [0 for _ in range (bucket_count)]
with open("mixmilk.in") as read:
    for i in range (bucket_count):
        capacity[i], milk[i] = map(int, read.readline().split())
for i in range (turn_count):
    x = min(milk[i%bucket_count], capacity[(i+1)%3]-milk[(i+1)%bucket_count])
    milk[(i+1)%bucket_count] += x
    milk[(i)%bucket_count] -= x
with open("mixmilk.out", "w") as out:
    for m in milk:
        print(m, file=out)