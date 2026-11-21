`timescale 1ns/1ps

module mac_pipeline_equivalence_tb #(
    parameter INPUT_WIDTH  = 8,
    parameter INPUT_FRAC   = 4,
    parameter ACC_WIDTH    = 24,
    parameter ACC_FRAC     = 8,
    parameter OUTPUT_WIDTH = 8,
    parameter OUTPUT_FRAC  = 4
);

    logic clk;
    logic rst;

    logic clear_acc;
    logic valid_in;

    logic signed [INPUT_WIDTH-1:0] A;
    logic signed [INPUT_WIDTH-1:0] B;

    logic signed [OUTPUT_WIDTH-1:0] Y;
    logic valid_out;

    integer file_handle;
    integer scan_result;

    integer clear_code;
    integer a_code;
    integer b_code;
    integer expected_code;

    integer checks;
    integer errors;

    mac_pipeline #(
        .INPUT_WIDTH(INPUT_WIDTH),
        .INPUT_FRAC(INPUT_FRAC),
        .ACC_WIDTH(ACC_WIDTH),
        .ACC_FRAC(ACC_FRAC),
        .OUTPUT_WIDTH(OUTPUT_WIDTH),
        .OUTPUT_FRAC(OUTPUT_FRAC)
    ) dut (
        .clk(clk),
        .rst(rst),
        .clear_acc(clear_acc),
        .valid_in(valid_in),
        .A(A),
        .B(B),
        .Y(Y),
        .valid_out(valid_out)
    );

    always #5 clk = ~clk;

    initial begin

        $dumpfile("results/mac_pipeline_equivalence.vcd");
        $dumpvars(0, mac_pipeline_equivalence_tb);

        clk = 0;
        rst = 1;

        clear_acc = 0;
        valid_in = 0;

        A = 0;
        B = 0;

        checks = 0;
        errors = 0;

        repeat (2) @(posedge clk);

        @(negedge clk);
        rst = 0;

        file_handle = $fopen("vectors/rtl_vectors.csv", "r");

        if (file_handle == 0) begin
            $display("ERROR: Cannot open CSV file");
            $finish;
        end

        while (!$feof(file_handle)) begin

            scan_result = $fscanf(
                file_handle,
                "%d,%d,%d,%d\n",
                clear_code,
                a_code,
                b_code,
                expected_code
            );

            if (scan_result == 4) begin

                @(negedge clk);

                clear_acc = clear_code;
                valid_in = 1;

                A = a_code;
                B = b_code;

                // Stage 1: Capture input product
                @(posedge clk);

                // Deassert valid before the next rising edge
                @(negedge clk);

                valid_in = 0;
                clear_acc = 0;

                // Stage 2: Accumulate and update output
                @(posedge clk);
                #1;

                checks = checks + 1;

                if (valid_out !== 1'b1) begin

                    errors = errors + 1;

                    $display(
                        "FAIL: Vector %0d - valid_out error",
                        checks
                    );

                end
                else if ($signed(Y) !== expected_code) begin

                    errors = errors + 1;

                    $display(
                        "FAIL: Vector %0d | A=%0d B=%0d | Expected=%0d Got=%0d",
                        checks,
                        a_code,
                        b_code,
                        expected_code,
                        $signed(Y)
                    );

                end
            end

        end

        $fclose(file_handle);

        $display("");
        $display("======================================");
        $display("RTL - PYTHON EQUIVALENCE VERIFICATION");
        $display("======================================");

        $display("INPUT_WIDTH : %0d", INPUT_WIDTH);
        $display("INPUT_FRAC  : %0d", INPUT_FRAC);
        $display("ACC_WIDTH   : %0d", ACC_WIDTH);
        $display("ACC_FRAC    : %0d", ACC_FRAC);
        $display("OUTPUT_WIDTH: %0d", OUTPUT_WIDTH);
        $display("OUTPUT_FRAC : %0d", OUTPUT_FRAC);

        $display("Total vectors : %0d", checks);
        $display("Errors        : %0d", errors);

        if (errors == 0)
            $display("EQUIVALENCE RESULT: PASS");
        else
            $display("EQUIVALENCE RESULT: FAIL");

        $finish;

    end

endmodule