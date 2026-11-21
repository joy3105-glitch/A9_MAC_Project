module mac_parameterized #(
    parameter INPUT_WIDTH  = 8,
    parameter INPUT_FRAC   = 4,

    parameter ACC_WIDTH    = 24,
    parameter ACC_FRAC     = 8,

    parameter OUTPUT_WIDTH = 8,
    parameter OUTPUT_FRAC  = 4
)(
    input  logic clk,
    input  logic rst,

    input  logic clear_acc,
    input  logic valid_in,

    input  logic signed [INPUT_WIDTH-1:0] A,
    input  logic signed [INPUT_WIDTH-1:0] B,

    output logic signed [OUTPUT_WIDTH-1:0] Y,
    output logic valid_out
);

    // ------------------------------------------------
    // 1. Internal widths and limits
    // ------------------------------------------------

    localparam PRODUCT_WIDTH = 2 * INPUT_WIDTH;

    localparam MAX_WIDTH =
        (ACC_WIDTH > PRODUCT_WIDTH) ? ACC_WIDTH : PRODUCT_WIDTH;

    localparam CALC_WIDTH = MAX_WIDTH + 2;

    localparam logic signed [ACC_WIDTH-1:0] ACC_MAX =
        {1'b0, {(ACC_WIDTH-1){1'b1}}};

    localparam logic signed [ACC_WIDTH-1:0] ACC_MIN =
        {1'b1, {(ACC_WIDTH-1){1'b0}}};

    localparam logic signed [OUTPUT_WIDTH-1:0] OUTPUT_MAX =
        {1'b0, {(OUTPUT_WIDTH-1){1'b1}}};

    localparam logic signed [OUTPUT_WIDTH-1:0] OUTPUT_MIN =
        {1'b1, {(OUTPUT_WIDTH-1){1'b0}}};

    localparam logic signed [CALC_WIDTH-1:0] ACC_MAX_EXT =
        {{(CALC_WIDTH-ACC_WIDTH){ACC_MAX[ACC_WIDTH-1]}}, ACC_MAX};

    localparam logic signed [CALC_WIDTH-1:0] ACC_MIN_EXT =
        {{(CALC_WIDTH-ACC_WIDTH){ACC_MIN[ACC_WIDTH-1]}}, ACC_MIN};

    localparam logic signed [CALC_WIDTH-1:0] OUTPUT_MAX_EXT =
        {{(CALC_WIDTH-OUTPUT_WIDTH){OUTPUT_MAX[OUTPUT_WIDTH-1]}},
          OUTPUT_MAX};

    localparam logic signed [CALC_WIDTH-1:0] OUTPUT_MIN_EXT =
        {{(CALC_WIDTH-OUTPUT_WIDTH){OUTPUT_MIN[OUTPUT_WIDTH-1]}},
          OUTPUT_MIN};


    // ------------------------------------------------
    // 2. Internal signals
    // ------------------------------------------------

    logic signed [PRODUCT_WIDTH-1:0] product;

    logic signed [CALC_WIDTH-1:0] product_ext;
    logic signed [CALC_WIDTH-1:0] product_scaled;

    logic signed [ACC_WIDTH-1:0] accumulator;

    logic signed [CALC_WIDTH-1:0] acc_base_ext;
    logic signed [CALC_WIDTH-1:0] sum_ext;
    logic signed [ACC_WIDTH-1:0] acc_next;

    logic signed [CALC_WIDTH-1:0] output_scaled;
    logic signed [OUTPUT_WIDTH-1:0] y_next;


    // ------------------------------------------------
    // 3. Fixed-point rescaling
    //    Rounding: nearest, ties away from zero
    // ------------------------------------------------

    function automatic logic signed [CALC_WIDTH-1:0]
        rescale_fixed(
            input logic signed [CALC_WIDTH-1:0] value,
            input integer shift_amount
        );

        logic signed [CALC_WIDTH-1:0] magnitude;
        logic signed [CALC_WIDTH-1:0] bias;

        begin
            if (shift_amount > 0) begin

                bias = '0;
                bias[0] = 1'b1;
                bias = bias <<< (shift_amount - 1);

                if (value >= 0) begin
                    rescale_fixed =
                        (value + bias) >>> shift_amount;
                end
                else begin
                    magnitude = -value;
                    rescale_fixed =
                        -((magnitude + bias) >>> shift_amount);
                end

            end
            else if (shift_amount < 0) begin

                rescale_fixed =
                    value <<< (-shift_amount);

            end
            else begin

                rescale_fixed = value;

            end
        end
    endfunction


    // ------------------------------------------------
    // 4. Multiplier
    // ------------------------------------------------

    always_comb begin
        product = A * B;

        product_ext =
            {{(CALC_WIDTH-PRODUCT_WIDTH){product[PRODUCT_WIDTH-1]}},
              product};

        // Product fractional bits = 2 * INPUT_FRAC
        // Convert product to accumulator fractional format

        product_scaled = rescale_fixed(
            product_ext,
            (2 * INPUT_FRAC) - ACC_FRAC
        );
    end


    // ------------------------------------------------
    // 5. Accumulator and saturation
    // ------------------------------------------------

    always_comb begin

        // clear_acc starts a new MAC sequence.
        // If clear_acc and valid_in are both high,
        // the current product is the first product.

        if (clear_acc)
            acc_base_ext = '0;
        else
            acc_base_ext =
                {{(CALC_WIDTH-ACC_WIDTH){accumulator[ACC_WIDTH-1]}},
                  accumulator};

        sum_ext = acc_base_ext + product_scaled;

        // Saturate accumulator

        if (sum_ext > ACC_MAX_EXT)
            acc_next = ACC_MAX;

        else if (sum_ext < ACC_MIN_EXT)
            acc_next = ACC_MIN;

        else
            acc_next = sum_ext[ACC_WIDTH-1:0];

    end


    // ------------------------------------------------
    // 6. Output rescaling and saturation
    // ------------------------------------------------

    always_comb begin

        output_scaled = rescale_fixed(
            {{(CALC_WIDTH-ACC_WIDTH){acc_next[ACC_WIDTH-1]}},
              acc_next},
            ACC_FRAC - OUTPUT_FRAC
        );

        if (output_scaled > OUTPUT_MAX_EXT)
            y_next = OUTPUT_MAX;

        else if (output_scaled < OUTPUT_MIN_EXT)
            y_next = OUTPUT_MIN;

        else
            y_next = output_scaled[OUTPUT_WIDTH-1:0];

    end


    // ------------------------------------------------
    // 7. Sequential logic
    // ------------------------------------------------

    always_ff @(posedge clk) begin

        if (rst) begin

            accumulator <= '0;
            Y           <= '0;
            valid_out   <= 1'b0;

        end
        else begin

            valid_out <= valid_in;

            if (clear_acc && !valid_in)
                accumulator <= '0;

            else if (valid_in) begin

                accumulator <= acc_next;
                Y           <= y_next;

            end

        end

    end

endmodule
