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


    // =====================================
    // Parameters
    // =====================================

    localparam PRODUCT_WIDTH =
        2 * INPUT_WIDTH;


    // =====================================
    // Internal signals
    // =====================================

    logic signed [PRODUCT_WIDTH-1:0]
        product;

    logic signed [ACC_WIDTH-1:0]
        accumulator;

    logic signed [ACC_WIDTH-1:0]
        acc_next;

    logic signed [ACC_WIDTH-1:0]
        scaled_value;


    // =====================================
    // Combinational logic
    // =====================================

    always_comb begin

        // Multiplication

        product = A * B;


        // MAC

        acc_next =
            accumulator + product;


        // Start with accumulator result

        scaled_value =
            acc_next;


        // =================================
        // Rounding
        // Q*.8 -> Q*.4
        // =================================

        if (scaled_value >= 0)

            scaled_value =
                scaled_value + 8;

        else

            scaled_value =
                scaled_value - 8;


        // =================================
        // Arithmetic shift
        // =================================

        scaled_value =
            scaled_value >>> 4;

    end


    // =====================================
    // Sequential logic
    // =====================================

    always_ff @(posedge clk) begin

        if (rst) begin

            accumulator <= '0;

            Y <= '0;

            valid_out <= 1'b0;

        end

        else begin

            valid_out <= valid_in;


            if (valid_in) begin

                accumulator <=
                    acc_next;


                // =================================
                // Output saturation
                // =================================

                if (scaled_value > 127)

                    Y <= 8'sd127;


                else if (scaled_value < -128)

                    Y <= -8'sd128;


                else

                    Y <=
                        scaled_value[7:0];

            end

        end

    end

endmodule
