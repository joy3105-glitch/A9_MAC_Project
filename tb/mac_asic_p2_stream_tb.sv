`timescale 1ns/1ps

module mac_asic_p2_stream_tb #(
    parameter INPUT_WIDTH  = 8,
    parameter INPUT_FRAC   = 4,
    parameter ACC_WIDTH    = 24,
    parameter ACC_FRAC     = 8,
    parameter OUTPUT_WIDTH = 8,
    parameter OUTPUT_FRAC  = 4,
    parameter MAX_VECTORS  = 2000
);

    reg clk;
    reg rst;
    reg valid_in;
    reg clear_acc;

    reg signed [INPUT_WIDTH-1:0] A;
    reg signed [INPUT_WIDTH-1:0] B;

    wire signed [OUTPUT_WIDTH-1:0] Y;
    wire valid_out;

    integer clear_codes [0:MAX_VECTORS-1];
    integer a_codes     [0:MAX_VECTORS-1];
    integer b_codes     [0:MAX_VECTORS-1];
    integer expected    [0:MAX_VECTORS-1];

    integer fd;
    integer scan_result;
    integer count;
    integer i;
    integer errors;
    integer checks;

    mac_pipeline2 dut (
        .clk(clk),
        .rst(rst),
        .valid_in(valid_in),
        .clear_acc(clear_acc),
        .A(A),
        .B(B),
        .Y(Y),
        .valid_out(valid_out)
    );

    always #5 clk = ~clk;

    initial begin
        clk       = 0;
        rst       = 1;
        valid_in  = 0;
        clear_acc = 0;
        A         = 0;
        B         = 0;

        count  = 0;
        errors = 0;
        checks = 0;

        fd = $fopen("vectors/rtl_vectors.csv", "r");

        if (fd == 0) begin
            $display("ERROR: Cannot open vectors/rtl_vectors.csv");
            $finish;
        end

        scan_result = $fscanf(fd, "%d,%d,%d,%d\n",
                               clear_codes[count],
                               a_codes[count],
                               b_codes[count],
                               expected[count]);

        while (scan_result == 4 && count < MAX_VECTORS) begin
            count = count + 1;

            if (count < MAX_VECTORS) begin
                scan_result = $fscanf(fd, "%d,%d,%d,%d\n",
                                       clear_codes[count],
                                       a_codes[count],
                                       b_codes[count],
                                       expected[count]);
            end
        end

        $fclose(fd);

        if (count < 3) begin
            $display("ERROR: Not enough test vectors.");
            $finish;
        end

        $display("========================================");
        $display("P2 PIPELINE STREAMING TEST");
        $display("Loaded vectors: %0d", count);
        $display("Expected latency: 3 cycles");
        $display("Expected initiation interval: 1 cycle");
        $display("========================================");

        // Reset.
        repeat (2) @(posedge clk);
        @(negedge clk);
        rst = 0;

        // Send one valid input on every clock cycle.
        for (i = 0; i < count; i = i + 1) begin
            @(negedge clk);

            valid_in  = 1;
            clear_acc = clear_codes[i];
            A         = a_codes[i];
            B         = b_codes[i];

            @(posedge clk);
            #1;

            if (i < 2) begin
                if (valid_out !== 1'b0) begin
                    errors = errors + 1;
                    $display("ERROR: Unexpected valid_out at input index %0d", i);
                end
            end else begin
                checks = checks + 1;

                if (valid_out !== 1'b1) begin
                    errors = errors + 1;
                    $display("ERROR: valid_out missing at output index %0d", i-2);
                end

                if ($signed(Y) !== expected[i-2]) begin
                    errors = errors + 1;
                    $display("ERROR: index=%0d expected=%0d got=%0d",
                             i-2, expected[i-2], $signed(Y));
                end
            end
        end

        // Stop input and drain the two remaining pipeline items.
        @(negedge clk);
        valid_in  = 0;
        clear_acc = 0;
        A         = 0;
        B         = 0;

        // First drain cycle: output the penultimate vector.
        @(posedge clk);
        #1;

        checks = checks + 1;

        if (valid_out !== 1'b1) begin
            errors = errors + 1;
            $display("ERROR: valid_out missing for output index %0d", count-2);
        end

        if ($signed(Y) !== expected[count-2]) begin
            errors = errors + 1;
            $display("ERROR: index=%0d expected=%0d got=%0d",
                     count-2, expected[count-2], $signed(Y));
        end

        // Second drain cycle: output the final vector.
        @(posedge clk);
        #1;

        checks = checks + 1;

        if (valid_out !== 1'b1) begin
            errors = errors + 1;
            $display("ERROR: valid_out missing for final output index %0d",
                     count-1);
        end

        if ($signed(Y) !== expected[count-1]) begin
            errors = errors + 1;
            $display("ERROR: final index=%0d expected=%0d got=%0d",
                     count-1, expected[count-1], $signed(Y));
        end

        $display("----------------------------------------");
        $display("Vectors loaded : %0d", count);
        $display("Output checks  : %0d", checks);
        $display("Errors         : %0d", errors);

        if (errors == 0)
            $display("P2 PIPELINE STREAMING TEST: PASS");
        else
            $display("P2 PIPELINE STREAMING TEST: FAIL");

        $display("========================================");

        $finish;
    end

endmodule
