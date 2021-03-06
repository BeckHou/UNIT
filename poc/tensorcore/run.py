import subprocess

workloads = [(1024,16,16,2048,1024,1,1,1,1),
(960,8,8,160,960,1,1,1,1),
(256,56,56,512,256,1,1,1,1),
(64,56,56,128,64,1,1,1,1),
(512,10,10,512,512,3,3,1,1),
(192,16,16,160,192,3,3,1,1),
(64,65,65,128,64,3,3,1,1),
(320,65,65,384,320,3,3,1,1),
(384,8,8,384,384,1,3,1,1),
(192,23,23,192,192,7,1,1,1),
(3,224,224,64,3,7,7,2,2),
(1024,15,15,2048,1024,1,1,2,2),
(128,65,65,256,128,3,3,2,2)]

workloads = [(1, 288, 35, 35, 384, 288, 3, 3, 2, 2), (1, 160, 9, 9, 224, 160, 3, 3, 1, 1), (1, 1056, 7, 7, 192, 1056, 1, 1, 1, 1), (1, 80, 73, 73, 192, 80, 3, 3, 1, 1), (1, 128, 16, 16, 128, 128, 3, 3, 1, 1), (1, 192, 16, 16, 192, 192, 3, 3, 1, 1), (1, 256, 16, 16, 256, 256, 3, 3, 1, 1), (1, 1024, 14, 14, 512, 1024, 1, 1, 1, 1), (1, 128, 16, 16, 160, 128, 3, 3, 1, 1), (1, 576, 14, 14, 192, 576, 1, 1, 1, 1), (1, 96, 16, 16, 128, 96, 3, 3, 1, 1), (1, 1024, 14, 14, 256, 1024, 1, 1, 1, 1), (1, 576, 14, 14, 128, 576, 1, 1, 1, 1), (1, 64, 29, 29, 96, 64, 3, 3, 1, 1), (1, 64, 56, 56, 128, 64, 1, 1, 2, 2), (1, 608, 14, 14, 192, 608, 1, 1, 1, 1)]

for i in workloads:
    res = []
    for dtype in [0, 2]:
        for tc in range(2 if dtype == 2 else 1):
            exec_time = []
            for algo in range(8):
                with open('input', 'w') as f:
                    #f.write('1\n')
                    for j in i:
                        f.write(str(j) + '\n')
                    f.write(str(dtype) + '\n')
                    f.write(str(algo) + '\n')
                    f.write(str(tc) + '\n')
                try:
                    proc = subprocess.check_output('./tensorcore.nvcc < input', shell=True).decode('utf-8')
                    proc = float(proc.split('\n')[0].lstrip('Exec: ').rstrip('us'))
                    exec_time.append(proc)
                except:
                    pass
            res.append(min(exec_time))
    print(i, ['fp32', None, 'fp16'][dtype], tc, res)
