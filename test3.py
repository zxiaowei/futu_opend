

def calc(*nums):
    sum = 0
    for n in nums:
        sum = sum + n

    return sum


print(calc(1,2,3,4))

print(calc(2,30,20,1))

l1 = [1,2,3,4,5,6]
print(calc(*l1))


def person(*args, **kwargs):
    for i in args:
        print(i)

    for k in kwargs:
        print("%s=%s" %(k, kwargs[k]))


person(1,2,3,4, aaa=33, bbb="bdfad")

def p2(aaa, *, city=None, job):
    print("%s %s" %(city, job))

p2(1, job=444)