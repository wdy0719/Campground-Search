read = open("shell.in")
n = int(read.readline())
shell_array = [i for i in range (3)]
counter = [0 for _ in range (3)]
for _ in range (n):
    a,b,g = [int(i)-1 for i in read.readline().split()]
    shell_array[a], shell_array[b] = shell_array[b], shell_array[a]
    counter[shell_array[g]] += 1
print(max(counter),file=open("shell.out", "w"))