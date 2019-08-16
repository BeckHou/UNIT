#include <cstdint>
#include <cassert>
#include <iostream>

#include "mkldnn.h"

#include "util.h"

int main() {
  int n = 4096, m = 4096, k = 4096;
  //std::cin >> n >> k >> m;

  int8_t *a = new int8_t[n * k];
  int8_t *b = new int8_t[m * k];
  int32_t *c = new int32_t[n * m];
  int32_t co = 0.0;

  mkldnn_status_t status = mkldnn_gemm_s8s8s32('N', 'T', 'F', n, m, k, 1.0,
                                  a, k, 0, b, k, 0, 0.0,
                                  c, m, &co);
  assert(status == mkldnn_success);

  {
    begin_roi();
    mkldnn_status_t status = mkldnn_gemm_s8s8s32('N', 'T', 'F', n, m, k, 1.0,
                                    a, k, 0, b, k, 0, 0.0,
                                    c, m, &co);
    assert(status == mkldnn_success);
    end_roi();
  }

  return 0;
}
