#!/usr/bin/python

from random import random

def get_value (x):
    return ord(str(x)[0])


# init means and data to random values
# use real data in your code
means = [random() for i in range(6)]
data = [1,2,3,4,5,6,7,8,9,10,11,12] #[random() for i in range(1000)]

param = 0.01 # bigger numbers make the means change faster
# must be between 0 and 1

print "before",means
for item in data:
    closest_k = 0;
    smallest_error = 9999; # this should really be positive infinity
    x = get_value(item)
    for k in enumerate(means):
        error = abs(x - get_value(k[1]))
        if error < smallest_error:
            smallest_error = error
            closest_k = k[0]
        means[closest_k] = get_value(means[closest_k])*(1-param) + x*(param)
print "after",means
#print data