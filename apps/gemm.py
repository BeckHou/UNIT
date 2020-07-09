import tvm
import tensorizer
from tvm import te
import numpy as np

from tvm import relay

n, m, k = 1, 1024, 1024

a = te.placeholder((n, k), dtype='uint8')
b = te.placeholder((m // 16, k // 4, 16, 4), dtype='int8')

r = te.reduce_axis((0, k))
c = te.compute((n, m), lambda x, y: te.sum(a[x, r].astype('int32') * b[y // 16, r // 4, y % 16, r % 4].astype('int32'), axis=r))

from tensorizer.intrinsics import INTRINSICS
from tensorizer.analyzer import analyze_tiling

sch = INTRINSICS['vnni']['schedule']([c])

#sch[c].parallel(sch[c].leaf_iter_vars[2])

with tvm.transform.PassContext(config={'tir.add_lower_pass': [(1, tensorizer.rewrite)]}, opt_level=3):
    ir = tvm.lower(sch, [a, b, c], simple_mode=True)
    module = tvm.build(sch, [a, b, c], target='llvm -mcpu=cascadelake')
    nda = tvm.nd.array((np.random.uniform(0, 1, (n, k)) * 32).astype('uint8'))
    ndb = tvm.nd.array((np.random.uniform(0, 1, (m // 16, k // 4, 16, 4)) * 32).astype('int8'))
    ndc = tvm.nd.array((np.random.uniform(0, 1, (n, m)) * 32).astype('int32'))
    ref = tvm.nd.array((np.random.uniform(0, 1, (n, m)) * 32).astype('int32'))
    timer = module.time_evaluator(module.entry_name, tvm.cpu(0), number=10, repeat=10)
    print(timer(nda, ndb, ndc).mean * 1e6)

# func = tvm.build(te.create_schedule(c.op), [a, b, c], target='llvm')
# timer = func.time_evaluator(func.entry_name, tvm.cpu(0))
# print(timer(nda, ndb, ref).mean)
#
# np.testing.assert_allclose(ndc.asnumpy(), ref.asnumpy())