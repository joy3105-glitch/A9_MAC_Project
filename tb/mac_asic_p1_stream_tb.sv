`timescale 1ns/1ps

module mac_asic_p1_stream_tb #(
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

    reg [8*256-1:0] header_line;

    mac_pipeline dut (
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

        // Skip CSV header.

        // Load all test vectors into arrays.
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

        if (count == 0) begin
            $display("ERROR: No test vectors loaded.");
            $finish;
        end

        $display("========================================");
        $display("P1 PIPELINE STREAMING TEST");
        $display("Loaded vectors: %0d", count);
        $display("========================================");

        // Reset.
        repeat (2) @(posedge clk);
        @(negedge clk);
        rst = 0;

        // Send one valid input on every clock cycle.
        for (i = 0; i < count; i = i + 1) begin
            @(negedge clk);

            valid_in = 1;
            clear_acc = clear_codes[i];
            A = a_codes[i];
            B = b_codes[i];

            @(posedge clk);
            #1;

            // P1 output corresponds to the previous input.
            if (i == 0) begin
                if (valid_out !== 1'b0) begin
                    errors = errors + 1;
                    $display("ERROR: valid_out should be 0 on first input cycle.");
                end
            end else begin
                checks = checks + 1;

                if (valid_out !== 1'b1) begin
                    errors = errors + 1;
                    $display("ERROR: valid_out missing at output index %0d", i-1);
                end

                if ($signed(Y) !== expected[i-1]) begin
                    errors = errors + 1;
                    $display("ERROR: index=%0d expected=%0d got=%0d",
                             i-1, expected[i-1], $signed(Y));
                end
            end
        end

        // Stop input and drain the final pipeline item.
        @(negedge clk);
        valid_in = 0;
        clear_acc = 0;
        A = 0;
        B = 0;

        @(posedge clk);
        #1;

        checks = checks + 1;

        if (valid_out !== 1'b1) begin
            errors = errors + 1;
            $display("ERROR: valid_out missing for final pipeline item.");
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
            $display("PIPELINE STREAMING TEST: PASS");
        else
            $display("PIPELINE STREAMING TEST: FAIL");

        $display("========================================");

        $finish;
    end

endmodule
