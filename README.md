# A9 – Fixed-Point MAC Datapath Design and Optimization

## Giới thiệu

Đồ án nghiên cứu thiết kế và tối ưu datapath Multiply-Accumulate
(MAC) sử dụng số học fixed-point, tập trung đánh giá ảnh hưởng
của bit-width và pipeline đến độ chính xác và chi phí phần cứng.

## Mục tiêu

- Xây dựng mô hình tham chiếu floating-point và fixed-point.
- Thiết kế MAC datapath bằng SystemVerilog.
- Kiểm chứng RTL với Golden Model Python.
- Khảo sát bit-width, fractional bits, rounding và overflow.
- So sánh các kiến trúc pipeline.
- Phân tích tài nguyên logic bằng Yosys.

## Các kiến trúc

| Kiến trúc | Mô tả | Latency |
|---|---|---|
| P0 | MAC parameterized | 1 cycle |
| P1 | MAC pipeline | 2 cycles |
| P2 | MAC pipeline 2 stages | 3 cycles |

## Cấu trúc dự án

- `python/`: Golden Model, kiểm chứng và các script khảo sát.
- `rtl/`: Các thiết kế RTL MAC.
- `tb/`: Testbench SystemVerilog.
- `vectors/`: Vector kiểm thử.
- `scripts/`: Script hỗ trợ tổng hợp.
- `results/`: CSV, log kiểm chứng, kết quả synthesis và biểu đồ.

## Công cụ

- Python 3
- Icarus Verilog
- Yosys
- Matplotlib
- Ubuntu / WSL

## Kết quả kiểm chứng

Các kiến trúc P0, P1 và P2 đều có kết quả PASS
trên năm cấu hình C1–C5.

- P0: 5/5 cấu hình PASS.
- P1: 5/5 cấu hình PASS.
- P2: 5/5 cấu hình PASS.
- P1/P2 control tests: PASS.

Các kết quả chi tiết được lưu trong `results/`.

## Giới hạn hiện tại

Các thống kê generic cells của Yosys chưa tương đương
với LUT FPGA hoặc diện tích ASIC.

Các chỉ số timing/Fmax và đánh giá công nghệ đích
chưa được hoàn thiện.

## Trạng thái

Bản nghiên cứu và kiểm chứng tiến độ, chưa phải bản nghiệm thu cuối cùng.
