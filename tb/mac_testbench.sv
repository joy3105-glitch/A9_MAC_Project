
`timescale 1ns/1ps

module mac_testbench;

    logic clk = 0;
    logic rst;
    logic signed [7:0] A;
    logic signed [7:0] B;
    logic valid_in;
    logic signed [7:0] Y;
    logic valid_out;

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

    // Check after nonblocking assignments have updated outputs.
    always @(posedge clk) begin
        if (!rst && valid_in) begin
            case ({A, B})
                {8'sd20, 8'sd16}: begin
                    #1;
                    checks = checks + 1;
                    if (valid_out !== 1'b1 || Y !== 8'sd20) begin
                        $display("FAIL: Test 1, expected Y=20, got Y=%0d", Y);
                        errors = errors + 1;
                    end else begin
                        $display("PASS: Test 1, Y=%0d", Y);
                    end
                end

                {8'sd24, 8'sd8}: begin
                    #1;
                    checks = checks + 1;
                    if (valid_out !== 1'b1 || Y !== 8'sd32) begin
                        $display("FAIL: Test 2, expected Y=32, got Y=%0d", Y);
                        errors = errors + 1;
                    end else begin
                        $display("PASS: Test 2, Y=%0d", Y);
                    end
                end

                {-8'sd16, 8'sd16}: begin
                    #1;
                    checks = checks + 1;
                    if (valid_out !== 1'b1 || Y !== 8'sd16) begin
                        $display("FAIL: Test 3, expected Y=16, got Y=%0d", Y);
                        errors = errors + 1;
                    end else begin
                        $display("PASS: Test 3, Y=%0d", Y);
                    end
                end

                default: begin
                    $display("INFO: Unlisted input A=%0d B=%0d", A, B);
                end
            endcase
        end
    end

    initial begin
        rst = 1;
        valid_in = 0;
        A = 0;
        B = 0;

        repeat (2) @(negedge clk);
        rst = 0;

        @(negedge clk);
        A = 8'sd20;
        B = 8'sd16;
        valid_in = 1;

        @(negedge clk);
        A = 8'sd24;
        B = 8'sd8;

        @(negedge clk);
        A = -8'sd16;
        B = 8'sd16;

        @(negedge clk);
        valid_in = 0;
        A = 0;
        B = 0;

        repeat (2) @(negedge clk);

        $display("--------------------------------");
        $display("Checks = %0d, Errors = %0d", checks, errors);

        if (errors == 0 && checks == 3)
            $display("RTL TEST RESULT: PASS");
        else
            $display("RTL TEST RESULT: FAIL");

        $finish;
    end

endmodule
