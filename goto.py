"""
Author: Taine Zhao
License: BSD2
Descr: goto and label statements in Python 3.5+.
       The approach is robust and even works in bytecode file
       or compiled binary executables.
       However, be cautious when opening the door against
       "goto considered harmful".

e.g., in the following code, 'x = 1 + x' will be ignored.
```python
    @allow_goto
    def f(x):
        goto.a
        x = 1 + x
        label.a
        return x

    print(f(1)) #
```
"""
import bytecode
import types

from bytecode.instr import Instr

class GotoLabel:
    def __getattr__(self, x):
         raise NotImplementedError

goto = GotoLabel()
label = GotoLabel()
def _allow_goto(code: types.CodeType, globals: dict):
    bc = bytecode.Bytecode.from_code(code)
    jump_targets = {}
    ch = []
    state = None
    for i, each in enumerate(bc):
        if not isinstance(each, bytecode.Instr):
            continue
        if state is label and each.name == 'LOAD_ATTR':
            if each.arg in jump_targets:                        
                raise ValueError(
                    "duplicate label <{}> at "
                    "{}, line {}"
                    .format(each.arg, code.co_filename, each.lineno)
                )

            l = jump_targets[each.arg] = bytecode.Label()
            ch.append((i-1, bytecode.Instr("NOP", lineno=each.lineno)))
            ch.append((i, l))
            verify_i = bc[i+1]
            assert isinstance(verify_i, bytecode.Instr) and verify_i.name == 'POP_TOP', (
                "allow label.x syntax only at {}, line {}!"
                .format(code.co_filename, each.lineno)
            )
            ch.append((i + 1, bytecode.Instr("NOP")))
            state = None
            continue
        elif each.name == 'LOAD_GLOBAL' and globals.get(each.arg) is label:
            state = label

    for i, each in enumerate(bc):
        if not isinstance(each, bytecode.Instr):
            continue
        if state is goto and each.name == 'LOAD_ATTR':
            if each.arg not in jump_targets:                        
                raise ValueError(
                    "unknown jump target <{}> at "
                    "{}, line {}"
                    .format(each.arg, code.co_filename, each.lineno)
                )

            l = jump_targets[each.arg]
            ch.append((i-1, bytecode.Instr("NOP", lineno=each.lineno)))
            ch.append((i, bytecode.Instr("JUMP_ABSOLUTE", arg=l, lineno=each.lineno)))
            verify_i = bc[i+1]
            assert isinstance(verify_i, bytecode.Instr) and verify_i.name == 'POP_TOP', (
                "allow goto.x syntax only at {}, line {}!"
                .format(code.co_filename, each.lineno)
            )
            ch.append((i + 1, bytecode.Instr("NOP")))
            state = None
            continue
        elif each.name == 'LOAD_GLOBAL' and globals.get(each.arg) is goto:
            state = goto
    for i, o in ch:
        bc[i] = o
    
    cbc = bc.to_concrete_bytecode()
    cs = cbc.consts
    for i in range(len(cs)):
        sub_code = cs[i]
        if isinstance(sub_code, types.CodeType):
            cs[i] = _allow_goto(sub_code, globals)

    return cbc.to_code()

def allow_goto(f: types.FunctionType):
    assert isinstance(f, types.FunctionType), "expect a function, got a {}".format(f)
    f.__code__ = _allow_goto(f.__code__, f.__globals__)
    return f

if __name__ == '__main__':
    @allow_goto
    def f(x):
        goto.a
        x = 1 + x
        label.a
        return x

    print(f(1)) # 1
