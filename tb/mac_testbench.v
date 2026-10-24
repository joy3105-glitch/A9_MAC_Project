
`timescale 1ns/1ps

module mac_testbench;

    reg clk = 0;
    reg rst;
    reg signed [7:0] A, B;
    reg valid_in;

    wire signed [7:0] Y;
    wire valid_out;

    integer errors = 0;
    integer checks = 0;

    mac_baseline dut (
        .clk(clk),
        .rst(rst),
        .A(A),
        .B(B),
        .valid_in(valid_in),
        .Y(Y),
        .valid_out(valid_out)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("results/mac.vcd");
        $dumpvars(0, mac_testbench);
    end

    task check_result;
        input integer test_number;
        input integer expected;
        begin
            #1;
            checks = checks + 1;

            if (valid_out !== 1'b1 || Y !== expected) begin
                $display(
                    "FAIL: Test %0d, expected Y=%0d, got Y=%0d",
                    test_number, expected, Y
                );
                errors = errors + 1;
            end else begin
                $display(
                    "PASS: Test %0d, Y=%0d",
                    test_number, Y
                );
            end
        end
    endtask

    initial begin
        rst = 1;
        valid_in = 0;
        A = 0;
        B = 0;

        repeat (2) @(negedge clk);
        rst = 0;

        @(negedge clk);
        A = 20;
        B = 16;
        valid_in = 1;
        @(posedge clk);
        check_result(1, 20);

        @(negedge clk);
        A = 24;
        B = 8;
        @(posedge clk);
        check_result(2, 32);

        @(negedge clk);
        A = -16;
        B = 16;
        @(posedge clk);
        check_result(3, 16);

        @(negedge clk);
        valid_in = 0;
        A = 0;
        B = 0;

        repeat (2) @(negedge clk);

        $display("--------------------------------");
        $display("Checks = %0d, Errors = %0d",
                 checks, errors);

        if (errors == 0 && checks == 3)
            $display("RTL TEST RESULT: PASS");
        else
            $display("RTL TEST RESULT: FAIL");

        $finish;
    end

endmodule
