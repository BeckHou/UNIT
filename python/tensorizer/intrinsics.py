from tvm import te
import tvm
import functools

def _vnni():
    """ Define the stencil of VNNI. """
    a = te.placeholder((64, ), dtype='int8', name='a')
    b = te.placeholder((64, ), dtype='int8', name='b')
    red = te.reduce_axis((0, 4), name='red')
    c = te.compute((16, ),
            lambda x: te.sum(a[x * 4 + red].astype('int32') * b[x * 4 + red].astype('int32'),
                             axis=red),
            name='c')
    return c.op

def _index2ramps(index, axis, dtype=None):
    coef = tvm.arith.detect_linear_equation(index, [i[0] for i in axis])
    assert list(coef)
    x = 0
    base_dict = {}
    while x < len(axis) and isinstance(coef[x], tvm.tir.IntImm) and coef[x].value == 0:
        base_dict[axis[x][0]] = tvm.tir.IntImm('int32', 0)
        x += 1
    base_dict[axis[x][0]] = tvm.tir.IntImm('int32', 0)
    ramps = []
    
    stride = coef[x]
    trips = axis[x][2]

    if isinstance(stride, tvm.tir.IntImm):
        y = x + 1
        while y < len(axis) and isinstance(coef[y], tvm.tir.IntImm) and coef[y].value == stride.value * trips:
            trips *= axis[y][2]
            base_dict[axis[y][0]] = tvm.tir.IntImm('int32', 0)
            y += 1
        if y == len(axis):
            base_index = tvm.tir.stmt_functor.substitute(index, base_dict)
            ramp = tvm.tir.Ramp(base_index, stride, trips)
            return [ramp]

    def _iter_axis_dom(axis_dom):
        assignment = [m for _, m, _ in axis_dom]
        if assignment:
            while assignment[-1] != axis_dom[-1][2]:
                yield {i[0]: j for i, j in zip(axis_dom, assignment)}
                assignment[0] += 1
                for j in range(len(assignment) - 1):
                    if assignment[j] == axis_dom[j][2]:
                        assignment[j] = 0
                        assignment[j + 1] += 1
                    else:
                        break
        else:
            yield {}

    # TODO(were): Ramp only
    for i in _iter_axis_dom(axis[y:]):
        m = base_dict.copy()
        m.update(i)
        base_index = tvm.tir.stmt_functor.substitute(index, m)
        ramp = tvm.tir.Ramp(base_index, stride, trips)
        ramp = tvm.arith.Analyzer().canonical_simplify(ramp)
        ramps.append(ramp)

    return ramps

def _load_concatenator(load, axis, dtype=None):
    ramps = _index2ramps(load.index, axis)
    assert 'x' not in load.dtype
    loads = []
    total_lanes = 0
    for ramp in ramps:
        lanes = int(ramp.dtype.split('x')[1])
        dtype = load.dtype + 'x' + str(lanes)
        total_lanes += lanes
        loads.append(tvm.tir.Load(dtype, load.buffer_var, ramp))
    if len(loads) == 1:
        res = loads[0]
    res = tvm.tir.Shuffle(loads, list(range(total_lanes)))
    if dtype is not None:
        return tvm.tir.call_pure_intrin(dtype, 'reinterpret', res)
    return res

def _vnni_write(store, axis, operands):
    ramps = _index2ramps(store.index, axis)
    assert 'x' not in store.value.dtype
    assert len(ramps) == 1
    llvm_intrin = 'llvm.x86.avx512.vpdpbusd.512'
    vnni = tvm.tir.call_llvm_intrin('int32x16', llvm_intrin,
                                     tvm.tir.const(0, 'uint32'), *operands)
    return tvm.tir.Store(store.buffer_var, vnni, ramps[0])

def _vnni_init(store, axis):
    ramps = _index2ramps(store.index, axis)
    assert 'x' not in store.value.dtype
    assert len(ramps) == 1
    llvm_intrin = 'llvm.x86.avx512.vpdpbusd.512'
    return tvm.tir.Store(store.buffer_var, tvm.tir.const(0, 'int32x16'), ramps[0])

INTRINSICS = {
  'vnni': {
    'pattern': _vnni(),
    'operands': [
        functools.partial(_load_concatenator, dtype='int32x16'),
        functools.partial(_load_concatenator, dtype='int32x16')
    ],
    'write': _vnni_write,
    'init': _vnni_init
  },
}