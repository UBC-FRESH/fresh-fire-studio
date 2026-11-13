# P179.17 deterministic suppression queue

Status: diagnostic resource-queue module.

`suppression/queue.py` implements a non-preemptive discrete queue inspired by
Bookbinder and Martell's helitack queue:

- requests have arrival time, service time and priority;
- servers have availability windows;
- a request is assigned to the server that can start it earliest;
- higher priority requests are ordered first;
- requests that cannot finish inside a server window remain unserved;
- busy time is reported as utilization.

It does not model random arrivals, service distributions, preemption or
multiple incident queues.

Tests cover parallel servers, priority ordering, unserved requests and
utilization.

This is a scheduling primitive for a later full IA/aircraft dispatch model. It
does not change the P179 fire-growth results.
