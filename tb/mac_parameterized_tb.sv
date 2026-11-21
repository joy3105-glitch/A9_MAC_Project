`timescale 1ns/1ps

module mac_parameterized_tb;

    logic clk;
    logic rst;

    logic clear_acc;
    logic valid_in;

    logic signed [7:0] A;
    logic signed [7:0] B;

    logic signed [7:0] Y;
    logic valid_out;

    integer checks = 0;
    integer errors = 0;

    mac_parameterized dut (
        .clk(clk),
        .rst(rst),
        .clear_acc(clear_acc),
        .valid_in(valid_in),
        .A(A),
        .B(B),
        .Y(Y),
        .valid_out(valid_out)
    );

    // Clock: period = 10 ns
    always #5 clk = ~clk;


    // -----------------------------------------------
    // Test task
    // -----------------------------------------------

    task automatic run_case(
        input integer a_code,
        input integer b_code,
        input integer clear_value,
        input integer expected,
        input integer case_number
    );

        begin

            @(negedge clk);

            A         = a_code;
            B         = b_code;
            clear_acc = clear_value;
            valid_in  = 1'b1;

            @(posedge clk);
            #1;

            checks = checks + 1;

            if (valid_out !== 1'b1) begin

                errors = errors + 1;

                $display(
                    "FAIL: Test %0d, valid_out is not high",
                    case_number
                );

            end
            else if ($signed(Y) !== expected) begin

                errors = errors + 1;

                $display(
                    "FAIL: Test %0d, expected Y=%0d, got Y=%0d",
                    case_number,
                    expected,
                    $signed(Y)
                );

            end
            else begin

                $display(
                    "PASS: Test %0d, Y=%0d",
                    case_number,
                    $signed(Y)
                );

            end

            @(negedge clk);

            valid_in  = 1'b0;
            clear_acc = 1'b0;

        end

    endtask


    // -----------------------------------------------
    // Main test
    // -----------------------------------------------

    initial begin

        $dumpfile("results/mac_parameterized.vcd");
        $dumpvars(0, mac_parameterized_tb);

        clk       = 0;
        rst       = 1;

        clear_acc = 0;
        valid_in  = 0;

        A = 0;
        B = 0;

        repeat (2) @(posedge clk);

        @(negedge clk);
        rst = 0;


        // Test 1:
        // 1.25 * 1.0 = 1.25
        // Q4.4 output code = 20

        run_case(20, 16, 1, 20, 1);


        // Test 2:
        // New independent MAC:
        // 1.25 * 2.0 = 2.5
        // Output code = 40

        run_case(20, 32, 1, 40, 2);


        // Test 3:
        // Continue previous MAC:
        // 2.5 + (2.0 * 1.5) = 5.5
        // Output code = 88

        run_case(32, 24, 0, 88, 3);


        // Test 4:
        // New independent MAC:
        // (-1.0) * 2.0 = -2.0
        // Output code = -32

        run_case(-16, 32, 1, -32, 4);


        // Test 5:
        // 7.0 * 7.0 = 49.0
        // Output saturation: 7.9375
        // Output code = 127

        run_case(112, 112, 1, 127, 5);

                // Test 6:
        // Positive rounding tie:
        // 0.0625 * 0.5 = 0.03125
        // Round to nearest, ties away from zero
        // Output code = 1

        run_case(1, 8, 1, 1, 6);


        // Test 7:
        // Negative rounding tie:
        // -0.0625 * 0.5 = -0.03125
        // Round to nearest, ties away from zero
        // Output code = -1

        run_case(-1, 8, 1, -1, 7);


        // Test 8:
        // Negative output saturation:
        // -8.0 * 7.9375 = -63.5
        // Output saturates to -8.0
        // Output code = -128

        run_case(-128, 127, 1, -128, 8);


        // -------------------------------------------
        // Summary
        // -------------------------------------------

        $display("--------------------------------");
        $display("Checks = %0d, Errors = %0d", checks, errors);

        if (errors == 0)
            $display("PARAMETERIZED MAC TEST: PASS");
        else
            $display("PARAMETERIZED MAC TEST: FAIL");

        $finish;

    end

endmodule
