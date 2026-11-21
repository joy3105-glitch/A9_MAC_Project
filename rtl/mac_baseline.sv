
module mac_baseline #(
    parameter INPUT_WIDTH = 8,
    parameter ACC_WIDTH   = 24
)(
    input  logic clk,
    input  logic rst,

    input  logic signed [INPUT_WIDTH-1:0] A,
    input  logic signed [INPUT_WIDTH-1:0] B,
    input  logic valid_in,

    output logic signed [INPUT_WIDTH-1:0] Y,
    output logic valid_out
);

    localparam PRODUCT_WIDTH = 2 * INPUT_WIDTH;

    logic signed [PRODUCT_WIDTH-1:0] product;
    logic signed [ACC_WIDTH-1:0] accumulator;
    logic signed [ACC_WIDTH-1:0] acc_next;

    // One extra bit prevents overflow before saturation.
    logic signed [ACC_WIDTH:0] sum_ext;
    logic signed [ACC_WIDTH:0] product_ext;
    logic signed [ACC_WIDTH:0] rounded_value;

    logic signed [INPUT_WIDTH-1:0] y_next;

    localparam logic signed [ACC_WIDTH-1:0] ACC_MAX =
        {1'b0, {(ACC_WIDTH-1){1'b1}}};

    localparam logic signed [ACC_WIDTH-1:0] ACC_MIN =
        {1'b1, {(ACC_WIDTH-1){1'b0}}};

    always_comb begin
        // Signed multiplication: Q4.4 x Q4.4 -> Q8.8.
        product = A * B;

        // Extend both operands before addition.
        product_ext = {{(ACC_WIDTH + 1 - PRODUCT_WIDTH){product[PRODUCT_WIDTH-1]}}, product};

        sum_ext =
            $signed({accumulator[ACC_WIDTH-1], accumulator})
            + product_ext;

        // Saturate accumulator after every accepted product.
        if (sum_ext > $signed({ACC_MAX[ACC_WIDTH-1], ACC_MAX}))
            acc_next = ACC_MAX;
        else if (sum_ext < $signed({ACC_MIN[ACC_WIDTH-1], ACC_MIN}))
            acc_next = ACC_MIN;
        else
            acc_next = sum_ext[ACC_WIDTH-1:0];

        // Convert accumulator Q*.8 to output Q*.4.
        // Signed division truncates toward zero.
        // Adjust by half an LSB to round ties away from zero.
        if (acc_next >= 0)
            rounded_value = ($signed(acc_next) + 8) / 16;
        else
            rounded_value = ($signed(acc_next) - 8) / 16;

        // Saturate to the signed output width.
        if (rounded_value > 127)
            y_next = {1'b0, {(INPUT_WIDTH-1){1'b1}}};
        else if (rounded_value < -128)
            y_next = {1'b1, {(INPUT_WIDTH-1){1'b0}}};
        else
            y_next = rounded_value[INPUT_WIDTH-1:0];
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            accumulator <= '0;
            Y           <= '0;
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
