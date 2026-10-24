
module mac_baseline #(
    parameter INPUT_WIDTH = 8,
    parameter ACC_WIDTH   = 24
)(
    input  wire clk,
    input  wire rst,
    input  wire signed [INPUT_WIDTH-1:0] A,
    input  wire signed [INPUT_WIDTH-1:0] B,
    input  wire valid_in,
    output reg signed [INPUT_WIDTH-1:0] Y,
    output reg valid_out
);

    localparam PRODUCT_WIDTH = 2 * INPUT_WIDTH;

    reg signed [PRODUCT_WIDTH-1:0] product;
    reg signed [ACC_WIDTH-1:0] accumulator;
    reg signed [ACC_WIDTH-1:0] acc_next;

    reg signed [ACC_WIDTH:0] sum_ext;
    reg signed [ACC_WIDTH:0] product_ext;
    reg signed [ACC_WIDTH:0] rounded_value;

    reg signed [INPUT_WIDTH-1:0] y_next;

    localparam signed [ACC_WIDTH-1:0] ACC_MAX =
        {1'b0, {(ACC_WIDTH-1){1'b1}}};

    localparam signed [ACC_WIDTH-1:0] ACC_MIN =
        {1'b1, {(ACC_WIDTH-1){1'b0}}};

    always @(*) begin
        // Q4.4 x Q4.4 -> Q8.8
        product = A * B;

        // Extend the signed product to ACC_WIDTH + 1 bits.
        product_ext = {
            {(ACC_WIDTH + 1 - PRODUCT_WIDTH)
                {product[PRODUCT_WIDTH-1]}},
            product
        };

        // Add the product to the accumulator.
        sum_ext =
            {accumulator[ACC_WIDTH-1], accumulator}
            + product_ext;

        // Saturate the accumulator.
        if ($signed(sum_ext) > $signed({ACC_MAX[ACC_WIDTH-1], ACC_MAX})) acc_next = ACC_MAX;
        else if ($signed(sum_ext) < $signed({ACC_MIN[ACC_WIDTH-1], ACC_MIN}))
            acc_next = ACC_MIN;
        else
            acc_next = sum_ext[ACC_WIDTH-1:0];

        // Convert Q*.8 to Q*.4.
        // Round to nearest, ties away from zero.
        if (acc_next >= 0)
            rounded_value =
                ($signed({acc_next[ACC_WIDTH-1], acc_next}) + 8) / 16;
        else
            rounded_value =
                ($signed({acc_next[ACC_WIDTH-1], acc_next}) - 8) / 16;

        // Saturate the output to the signed output range.
        if ($signed(rounded_value) > 127)
            y_next = {1'b0, {(INPUT_WIDTH-1){1'b1}}};
        else if ($signed(rounded_value) < -128)
            y_next = {1'b1, {(INPUT_WIDTH-1){1'b0}}};
        else
            y_next = rounded_value[INPUT_WIDTH-1:0];
    end

    // Sequential logic: accumulator and output registers.
    always @(posedge clk) begin
        if (rst) begin
            accumulator <= 0;
            Y           <= 0;
            valid_out   <= 1'b0;
        end else begin
            valid_out <= valid_in;

            if (valid_in) begin
                accumulator <= acc_next;
                Y           <= y_next;
            end
        end
    end

endmodule
