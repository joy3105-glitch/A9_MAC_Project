set arch $::env(MAC_ARCH)
set cfg  $::env(MAC_CFG)

array set tops {
    P0 mac_parameterized
    P1 mac_pipeline
    P2 mac_pipeline2
}

set top $tops($arch)

puts "========== POWER $arch $cfg =========="

# Read technology library
read_liberty /work/liberty/sky130_hd_tt_mac.lib

# Read mapped ASIC netlist
read_verilog /work/results/asic_sky130_filtered/${arch}_${cfg}_mapped.v

link_design $top

# Clock: 50 MHz
create_clock -name clk -period 20 [get_ports clk]

# Timing constraints
set_input_delay 1 -clock clk [get_ports {A* B* clear_acc valid_in}]
set_input_delay 0 -clock clk [get_ports rst]

set_output_delay 1 -clock clk [get_ports {Y* valid_out}]

set_false_path -from [get_ports rst]

# Vectorless input switching activity
set_power_activity -input_ports [get_ports {A* B*}] \
    -activity 0.1 -duty 0.5

# Continuous valid input
set_power_activity -input_ports [get_ports valid_in] \
    -activity 0.0 -duty 1.0

# Occasional accumulator clear
set_power_activity -input_ports [get_ports clear_acc] \
    -activity 0.01 -duty 0.01

# Reset inactive during normal operation
set_power_activity -input_ports [get_ports rst] \
    -activity 0.0 -duty 0.0

puts "========== POWER CONDITIONS =========="
puts "Clock frequency: 50 MHz"
puts "Data input activity: 0.1"
puts "Data input duty: 0.5"
puts "Method: Vectorless power estimation"

puts "========== POWER REPORT =========="

report_power -digits 6

puts "========== POWER COMPLETE =========="
