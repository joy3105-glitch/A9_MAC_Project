# A9 – Thiết kế và tối ưu datapath Multiply-Accumulate fixed-point cho FPGA và ASIC

**English:** Design and Optimization of a Fixed-Point Multiply-Accumulate Datapath for FPGA and ASIC

## 1. Mục tiêu đề tài

Xây dựng datapath Multiply-Accumulate (MAC) sử dụng số học
fixed-point và khảo sát ảnh hưởng của bit-width và pipeline
đến độ chính xác tính toán và chi phí phần cứng.

Các nhiệm vụ chính:
- Xây dựng reference arithmetic model.
- Thiết kế multiplier, accumulator và register/pipeline.
- Khảo sát truncation, rounding và saturation.
- Đánh giá nhiều cấu hình bit-width và pipeline.
- Tổng hợp và so sánh FPGA/ASIC.
- Phân tích numerical error, PPA, Fmax và latency.
- Đề xuất cấu hình phù hợp với các mục tiêu thiết kế.

## 2. Công cụ

- Python 3 và Matplotlib: golden model, numerical analysis.
- SystemVerilog: RTL MAC và testbench.
- Icarus Verilog: functional verification.
- Yosys: logic synthesis và technology mapping.
- nextpnr: FPGA implementation và timing.
- OpenSTA: ASIC static timing analysis.
- SKY130 HD Liberty: ASIC standard-cell library.
- Ubuntu/WSL và Docker: môi trường thực nghiệm.

## 3. Đặc tả số học fixed-point

Cấu hình tham chiếu ban đầu:

| Thành phần | Width | Fixed-point format |
|---|---:|---|
| Input | 8 | Q4.4 |
| Product | 16 | Q8.8 |
| Accumulator | 24 | Q16.8 |
| Output | 8 | Q4.4 |

Chính sách mặc định:
- Rounding: nearest, ties away from zero.
- Accumulator overflow: saturate_each_step.
- Input/output conversion: saturation.

Ngoài cấu hình tham chiếu, các khảo sát bit-width sử dụng
các độ rộng accumulator khác nhau.

## 4. Cấu hình bit-width

| Config | Input width | Fractional bits | Product width | Accumulator width |
|---|---:|---:|---:|---:|
| C1 | 6 | 2 | 12 | 15 |
| C2 | 8 | 4 | 16 | 19 |
| C3 | 10 | 6 | 20 | 23 |
| C4 | 12 | 8 | 24 | 27 |
| C5 | 16 | 12 | 32 | 35 |

Output trong bit-width sweep được giữ ở Q4.4.

## 5. Kiến trúc MAC

| Architecture | RTL | Latency | II |
|---|---|---:|---:|
| P0 | rtl/mac_parameterized.sv | 1 cycle | 1 |
| P1 | rtl/mac_pipeline.sv | 2 cycles | 1 |
| P2 | rtl/mac_pipeline2.sv | 3 cycles | 1 |

- P0: MAC parameterized, không bổ sung pipeline.
- P1: đăng ký kết quả product đã rescale trước accumulation.
- P2: bổ sung tầng thanh ghi đầu vào trước multiplication.

Các kiến trúc được so sánh về latency, throughput,
tài nguyên phần cứng và timing.

## 6. Reference model và verification

Reference model:
- python/numeric_spec.py
- python/golden_model.py
- python/verify_results.py

Verification:
- RTL equivalence với Python golden model.
- Self-checking SystemVerilog testbenches.
- Streaming pipeline verification.
- ASIC mapped gate-level verification.

Kết quả đã ghi nhận:
- P0: 5/5 cấu hình PASS.
- P1: 5/5 cấu hình PASS.
- P2: 5/5 cấu hình PASS.
- 655 verification vectors cho mỗi cấu hình.
- ASIC gate-level verification: 15/15 PASS.

## 7. Numerical error analysis

Các khảo sát:
- Bit-width sweep.
- Fractional-bit sweep.
- Rounding/truncation comparison.
- Overflow/saturation comparison.

| Config | MAE |
|---|---:|
| C1 | 0.099481 |
| C2 | 0.028077 |
| C3 | 0.016526 |
| C4 | 0.015649 |
| C5 | 0.015588 |

Các chỉ số chi tiết gồm MAE, MSE, RMSE và Max Error.

Nguồn dữ liệu:
- results/bitwidth_sweep.csv
- results/fractional_sweep.csv
- results/rounding_sweep.csv
- results/overflow_sweep.csv

## 8. FPGA synthesis và timing

Target: Lattice iCE40 HX8K.

Flow: Yosys + nextpnr.

Các chỉ số:
- LUT4.
- Flip-flops.
- Carry cells.
- Fmax.
- Timing status tại 50 MHz.

Kết quả:
results/fpga_ice40/fpga_ice40_summary.csv

## 9. ASIC synthesis và STA

Technology: SKY130 HD, TT Liberty corner.

Flow: Yosys technology mapping + OpenSTA.

Các chỉ số:
- Standard-cell count.
- Flip-flop count.
- Standard-cell area.
- Setup slack.
- Register-to-register timing.
- Estimated register-to-register Fmax.

Kết quả:
- results/asic_sky130_filtered/asic_sky130_summary.csv
- results/asic_sky130_filtered/timing/

Lưu ý: ASIC Fmax là ước lượng từ mapped-netlist STA,
không phải signoff Fmax sau physical implementation.
ASIC area là tổng diện tích standard cells,
không phải diện tích physical core.

## 10. PPA/Fmax/latency comparison

Bảng tổng hợp 15 cấu hình:
results/ppa_summary.csv

Các biểu đồ:
results/ppa_plots/

Phân tích Pareto:
results/asic_pareto_summary.csv

ASIC Pareto sử dụng ba tiêu chí:
- Minimize MAE.
- Minimize standard-cell area.
- Maximize estimated register-to-register Fmax.

Kết quả hiện tại: 14/15 cấu hình không bị chi phối
theo ba tiêu chí đã chọn.

## 11. Optimization recommendation

Các ứng viên dựa trên kết quả thực nghiệm:

- P1-C2: ưu tiên ASIC area khi MAE <= 0.03.
- P1-C3: cân bằng accuracy và ASIC area.
- P0-C3: ưu tiên ASIC timing khi MAE <= 0.02.
- P1-C3: ưu tiên FPGA Fmax khi MAE <= 0.02.

Không có một kiến trúc tối ưu tuyệt đối cho mọi tiêu chí.

## 12. Cấu trúc dự án

- python/: golden model và analysis scripts.
- rtl/: SystemVerilog MAC implementations.
- tb/: verification testbenches.
- vectors/: verification vectors.
- scripts/: synthesis, verification và STA scripts.
- liberty/: ASIC technology library.
- results/: synthesis reports, logs, CSV và plots.
- archive/: dữ liệu cũ.
- backup/: các bản sao lưu.

## 13. Hướng dẫn tái lập

Chạy từ thư mục gốc dự án.

Kiểm tra golden model:

    python3 python/numeric_spec.py
    python3 python/golden_model.py
    python3 python/verify_results.py

Khảo sát bit-width:

    python3 python/bitwidth_sweep.py

Tổng hợp PPA:

    python3 python/build_ppa_summary.py

Tạo biểu đồ và Pareto:

    python3 python/plot_ppa_pareto.py

Các flow FPGA/ASIC được thực hiện bằng script trong
scripts/ và yêu cầu cấu hình môi trường tương ứng.

## 14. Giới hạn và hướng phát triển

- Numerical error phụ thuộc bộ dữ liệu kiểm thử.
- FPGA và ASIC sử dụng các flow timing khác nhau.
- ASIC chưa được đánh giá bằng physical signoff.
- Pareto phụ thuộc tập tiêu chí tối ưu.
- MAC array hoặc dot-product engine là hướng mở rộng,
  không thuộc yêu cầu bắt buộc của đề tài.

## 15. Tiến độ thực hiện

Đã hoàn thành các thực nghiệm chính:
- Golden model.
- Parameterized RTL MAC.
- Verification vectors và equivalence.
- Numerical error analysis.
- FPGA/ASIC synthesis.
- PPA/Fmax/latency comparison.
- Optimization recommendation sơ bộ.

Các kết quả trên phản ánh tiến độ thực nghiệm hiện tại, chưa phải kết luận tối ưu cuối cùng của đồ án.

Các bước nghiên cứu và đánh giá tiếp theo sẽ được thực hiện theo yêu cầu đề tài A9.
