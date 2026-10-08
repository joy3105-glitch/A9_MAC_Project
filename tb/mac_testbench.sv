`timescale 1ns/1ps


module mac_testbench;


    // =====================================
    // Signals
    // =====================================

    logic clk;

    logic rst;

    logic signed [7:0] A;

    logic signed [7:0] B;

    logic valid_in;

    logic signed [7:0] Y;

    logic valid_out;


    // =====================================
    // DUT
    // =====================================

    mac_baseline dut (

        .clk(clk),

        .rst(rst),

        .A(A),

        .B(B),

        .valid_in(valid_in),

        .Y(Y),

        .valid_out(valid_out)

    );


    // =====================================
    // Clock
    // =====================================

    initial begin

        clk = 0;

        forever #5 clk = ~clk;

    end


    // =====================================
    // Waveform
    // =====================================

    initial begin

        $dumpfile(
            "results/mac.vcd"
        );

        $dumpvars(
            0,
            mac_testbench
        );

    end


    // =====================================
    // Test sequence
    // =====================================

    initial begin

        // Initial values

        rst = 1;

        valid_in = 0;

        A = 0;

        B = 0;


        // Reset

        #20;

        rst = 0;


        // =================================
        // Test 1
        // A = 20 / 16 = 1.25
        // B = 16 / 16 = 1.00
        // Product = 1.25
        // =================================

        @(negedge clk);

        A = 8'sd20;

        B = 8'sd16;

        valid_in = 1;


        // =================================
        // Test 2
        // A = 24 / 16 = 1.5
        // B = 8 / 16 = 0.5
        // =================================

        @(negedge clk);

        A = 8'sd24;

        B = 8'sd8;


        // =================================
        // Test 3
        // A = -16 / 16 = -1
        // B = 16 / 16 = 1
        // =================================

        @(negedge clk);

        A = -8'sd16;

        B = 8'sd16;


        // Stop valid

        @(negedge clk);

        valid_in = 0;


        // Wait

        #50;


        $finish;

    end


    // =====================================
    // Display
    // =====================================

    always @(posedge clk) begin

        if (valid_out) begin

            $display(
                "TIME=%0t | A=%0d | B=%0d | Y=%0d",
                $time,
                A,
                B,
                Y
            );

        end

    end


endmodule
