module mac_boundary_tb;

    logic clk = 0;
    logic rst = 0;
    logic clear_acc = 0;
    logic valid_in = 0;

    logic signed [7:0] A = 0;
    logic signed [7:0] B = 0;

    logic signed [7:0] Y;
    logic valid_out;

    integer checks = 0;
    integer errors = 0;

    // ACC_WIDTH = 12 để dễ kiểm tra accumulator saturation.
    mac_parameterized #(
        .INPUT_WIDTH  (8),
        .INPUT_FRAC   (4),
        .ACC_WIDTH    (12),
        .ACC_FRAC     (8),
        .OUTPUT_WIDTH (8),
        .OUTPUT_FRAC  (4)
    ) dut (
        .clk       (clk),
        .rst       (rst),
        .clear_acc (clear_acc),
        .valid_in  (valid_in),
        .A         (A),
        .B         (B),
        .Y         (Y),
        .valid_out (valid_out)
    );

    always #5 clk = ~clk;

    task automatic check_cycle;
        input logic clear_value;
        input logic valid_value;
        input integer a_value;
        input integer b_value;
        input integer expected_y;
        input logic expected_valid;
        input integer test_id;

        begin
            @(negedge clk);

            clear_acc = clear_value;
            valid_in  = valid_value;
            A         = a_value;
            B         = b_value;

            @(posedge clk);
            #1;

            checks = checks + 1;

            if ((Y !== expected_y[7:0]) ||
                (valid_out !== expected_valid)) begin

                errors = errors + 1;

                $display(
                    "FAIL Test %0d: Y=%0d, valid_out=%0b, expected Y=%0d, valid_out=%0b",
                    test_id, Y, valid_out,
                    expected_y, expected_valid
                );
            end
            else begin
                $display(
                    "PASS Test %0d: Y=%0d, valid_out=%0b",
                    test_id, Y, valid_out
                );
            end
        end
    endtask

    initial begin

        $display("==================================");
        $display("MAC BOUNDARY TEST");
        $display("==================================");

        // Test 1: Synchronous reset
        rst = 1;
        @(posedge clk);
        #1;

        checks = checks + 1;

        if ((Y !== 8'sd0) || (valid_out !== 1'b0)) begin
            errors = errors + 1;
            $display("FAIL Test 1: Reset");
        end
        else begin
            $display("PASS Test 1: Reset");
        end

        @(negedge clk);
        rst = 0;

        // Test 2: First product after reset.
        // 20/16 * 16/16 = 1.25 => output code 20.
        check_cycle(1, 1, 20, 16, 20, 1, 2);

        // Test 3: valid_in = 0.
        // Y must hold its previous value.
        check_cycle(0, 0, 127, 127, 20, 0, 3);

        // Test 4: Accumulator must retain its previous value.
        // 1.25 + 1.0 = 2.25 => output code 36.
        check_cycle(0, 1, 16, 16, 36, 1, 4);

        // Test 5: clear_acc and valid_in are both high.
        // New accumulation starts with the current product.
        check_cycle(1, 1, 16, 16, 16, 1, 5);

        // Test 6: clear_acc = 1, valid_in = 0.
        // Accumulator clears, but Y holds its previous value.
        check_cycle(1, 0, 0, 0, 16, 0, 6);

        // Test 7: Confirm accumulator was cleared.
        check_cycle(0, 1, 16, 16, 16, 1, 7);

        // Test 8: Positive accumulator saturation.
        // 7.0 * 7.0 = 49.0, accumulator saturates to its maximum.
        // Output also saturates to +127.
        check_cycle(1, 1, 112, 112, 127, 1, 8);

        // Test 9: Add -1.0 after positive accumulator saturation.
        // Saturated accumulator: 7.996... - 1.0 = 6.996...
        // Rounded output code = 112.
        check_cycle(0, 1, -16, 16, 112, 1, 9);

        // Test 10: Negative accumulator saturation.
        // -7.0 * 7.0 = -49.0, accumulator saturates to -8.0.
        check_cycle(1, 1, -112, 112, -128, 1, 10);

        // Test 11: Add +1.0 after negative accumulator saturation.
        // -8.0 + 1.0 = -7.0 => output code -112.
        check_cycle(0, 1, 16, 16, -112, 1, 11);

        $display("----------------------------------");
        $display("Checks : %0d", checks);
        $display("Errors : %0d", errors);

        if (errors == 0)
            $display("BOUNDARY TEST RESULT: PASS");
        else
            $display("BOUNDARY TEST RESULT: FAIL");

        $finish;
    end

endmodule
