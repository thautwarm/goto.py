# goto.py

A modern implementation of real goto/label statements in python 3.5+.


```python
@allow_goto
def f(x):
    if x > 2:
        goto.ret
    x *= 2
    label.ret
    return x

print(f(3)) # 3
print(f(2)) # 4
```
