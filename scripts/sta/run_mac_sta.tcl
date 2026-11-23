set arch $::env(MAC_ARCH)
set cfg  $::env(MAC_CFG)

array set tops {
    P0 mac_parameterized
    P1 mac_pipeline
    P2 mac_pipeline2
}

set top $tops($arch)

puts "========== STA $arch $cfg =========="

read_liberty /work/liberty/sky130_hd_tt_mac.lib

read_verilog /work/results/asic_sky130_filtered/${arch}_${cfg}_mapped.v

link_design $top

create_clock -name clk -period 20 [get_ports clk]

set_input_delay 1 -clock clk [get_ports {A* B* clear_acc valid_in}]
set_input_delay 0 -clock clk [get_ports rst]

set_output_delay 1 -clock clk [get_ports {Y* valid_out}]

set_false_path -from [get_ports rst]

check_setup

puts "========== OVERALL TIMING =========="
report_checks -path_delay max -group_count 1
report_worst_slack -max
report_tns

puts "========== REG TO REG TIMING =========="
report_checks -path_delay max \
    -from [all_registers -clock_pins] \
    -to [all_registers -data_pins] \
    -group_count 1

puts "========== STA COMPLETE =========="
