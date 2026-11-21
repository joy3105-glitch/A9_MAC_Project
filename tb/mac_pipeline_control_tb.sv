`timescale 1ns/1ps

module mac_pipeline_control_tb #(
    parameter PIPELINE = 1
);

    localparam LATENCY = (PIPELINE == 1) ? 1 : 2;

    reg clk = 0;
    always #5 clk = ~clk;

    reg rst = 1;
    reg clear_acc = 0;
    reg valid_in = 0;
    reg signed [7:0] A = 0;
    reg signed [7:0] B = 0;

    wire signed [7:0] Y;
    wire valid_out;

    generate
        if (PIPELINE == 1) begin : gen_p1
            mac_pipeline dut (
                .clk(clk), .rst(rst),
                .clear_acc(clear_acc), .valid_in(valid_in),
                .A(A), .B(B),
                .Y(Y), .valid_out(valid_out)
            );
        end else begin : gen_p2
            mac_pipeline2 dut (
                .clk(clk), .rst(rst),
                .clear_acc(clear_acc), .valid_in(valid_in),
                .A(A), .B(B),
                .Y(Y), .valid_out(valid_out)
            );
        end
    endgenerate

    integer errors = 0;
    integer checks = 0;
    integer acc_ref = 0;
    integer next_acc;
    integer product;
    integer expected_y;
    integer expected_output_hold = 0;
    integer i;

    reg [LATENCY:0] expected_valid_pipe;
    integer expected_data_pipe [0:LATENCY];

    function integer saturate8(input integer value);
        begin
            if (value > 127)
                saturate8 = 127;
            else if (value < -128)
                saturate8 = -128;
            else
                saturate8 = value;
        end
    endfunction

    function integer round_q8_to_q4(input integer value);
        begin
            if (value >= 0)
                round_q8_to_q4 = (value + 8) >>> 4;
            else
                round_q8_to_q4 = -((-value + 8) >>> 4);
        end
    endfunction

    task automatic step(
        input reg reset_value,
        input reg clear_value,
        input reg valid_value,
        input integer a_value,
        input integer b_value
    );
        integer j;
        begin
            @(negedge clk);

            rst = reset_value;
            clear_acc = clear_value;
            valid_in = valid_value;
            A = a_value;
            B = b_value;

            if (rst) begin
                acc_ref = 0;
                expected_output_hold = 0;
                expected_valid_pipe = 0;

                for (j = 0; j <= LATENCY; j = j + 1)
                    expected_data_pipe[j] = 0;
            end else begin
                if (clear_value)
                    next_acc = 0;
                else
                    next_acc = acc_ref;

                if (valid_value) begin
                    product = a_value * b_value;
                    next_acc = next_acc + product;

                    if (next_acc > 8388607)
                        next_acc = 8388607;
                    else if (next_acc < -8388608)
                        next_acc = -8388608;

                    acc_ref = next_acc;

                    expected_y = saturate8(
                        round_q8_to_q4(acc_ref)
                    );
                end else begin
                    if (clear_value)
                        acc_ref = 0;

                    expected_y = expected_output_hold;
                end

                for (j = LATENCY; j > 0; j = j - 1) begin
                    expected_valid_pipe[j] =
                        expected_valid_pipe[j-1];

                    expected_data_pipe[j] =
                        expected_data_pipe[j-1];
                end

                expected_valid_pipe[0] = valid_value;
                expected_data_pipe[0] = expected_y;
            end

            @(posedge clk);
            #1;

            checks = checks + 1;

            if (valid_out !== expected_valid_pipe[LATENCY]) begin
                errors = errors + 1;
                $display(
                    "FAIL valid cycle=%0d expected=%0b got=%0b",
                    checks,
                    expected_valid_pipe[LATENCY],
                    valid_out
                );
            end

            if (rst) begin
                if (Y !== 0) begin
                    errors = errors + 1;
                    $display("FAIL reset Y=%0d", $signed(Y));
                end
            end else begin
                if ($signed(Y) !==
                    (expected_valid_pipe[LATENCY]
                        ? expected_data_pipe[LATENCY]
                        : expected_output_hold)) begin
                    errors = errors + 1;
                    $display(
                        "FAIL data cycle=%0d expected=%0d got=%0d",
                        checks,
                        expected_data_pipe[LATENCY],
                        $signed(Y)
                    );
                end
            end

            if (rst)
                expected_output_hold = 0;
            else if (expected_valid_pipe[LATENCY])
                expected_output_hold =
                    expected_data_pipe[LATENCY];
        end
    endtask

    initial begin
        expected_valid_pipe = 0;

        for (i = 0; i <= LATENCY; i = i + 1)
            expected_data_pipe[i] = 0;

        step(1, 0, 0, 0, 0);
        step(1, 0, 0, 0, 0);

        // Continuous valid transactions.
        step(0, 1, 1, 16, 16);
        step(0, 0, 1, 16, 16);
        step(0, 0, 1, -8, 16);

        // Bubble.
        step(0, 0, 0, 0, 0);
        step(0, 0, 0, 0, 0);

        // Resume accumulation.
        step(0, 0, 1, 8, 16);

        // Clear without valid.
        step(0, 1, 0, 0, 0);
        step(0, 0, 0, 0, 0);

        // New sequence.
        step(0, 1, 1, -16, 16);
        step(0, 0, 1, -16, 16);

        // Reset while transactions are in flight.
        step(0, 0, 1, 32, 16);
        step(1, 0, 0, 0, 0);

        // Resume after reset.
        step(0, 1, 1, 16, 16);
        step(0, 0, 1, 8, 16);

        // Drain pipeline.
        repeat (4)
            step(0, 0, 0, 0, 0);

        $display("--------------------------------");
        $display("PIPELINE CONTROL TEST P%0d", PIPELINE);
        $display("Checks : %0d", checks);
        $display("Errors : %0d", errors);

        if (errors == 0)
            $display("CONTROL TEST: PASS");
        else
            $display("CONTROL TEST: FAIL");

        $finish;
    end

endmodule
