import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from golden_model import mac_fixed
from numeric_spec import OUTPUT_WIDTH, OUTPUT_FRAC

OUTPUT_FILE = Path("vectors/rtl_vectors.csv")

NUM_SEQUENCES = 100
MIN_LENGTH = 1
MAX_LENGTH = 12
RANDOM_SEED = 42


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate RTL test vectors for a configurable MAC."
    )

    parser.add_argument("--input-width", type=int, default=8)
    parser.add_argument("--input-frac", type=int, default=4)
    parser.add_argument("--acc-width", type=int, default=24)
    parser.add_argument("--acc-frac", type=int, default=8)

    return parser.parse_args()


def main():
    args = parse_args()

    input_width = args.input_width
    input_frac = args.input_frac
    acc_width = args.acc_width
    acc_frac = args.acc_frac

    if input_width < 2 or not 0 <= input_frac < input_width:
        raise ValueError("Invalid input width or fractional bits.")

    if acc_width < 2 or not 0 <= acc_frac < acc_width:
        raise ValueError("Invalid accumulator width or fractional bits.")

    random.seed(RANDOM_SEED)

    input_min = -(2 ** (input_width - 1))
    input_max = (2 ** (input_width - 1)) - 1

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    total_vectors = 0

    with OUTPUT_FILE.open("w", newline="") as file:
        writer = csv.writer(file)

        for sequence in range(NUM_SEQUENCES):
            length = random.randint(MIN_LENGTH, MAX_LENGTH)

            a_codes = []
            b_codes = []

            for index in range(length):
                a_code = random.randint(input_min, input_max)
                b_code = random.randint(input_min, input_max)

                a_codes.append(a_code)
                b_codes.append(b_code)

                a_real = [
                    code / (2 ** input_frac) for code in a_codes
                ]
                b_real = [
                    code / (2 ** input_frac) for code in b_codes
                ]

                expected = mac_fixed(
                    a_real,
                    b_real,
                    input_width=input_width,
                    input_frac=input_frac,
                    product_width=2 * input_width,
                    product_frac=2 * input_frac,
                    acc_width=acc_width,
                    acc_frac=acc_frac,
                    output_width=OUTPUT_WIDTH,
                    output_frac=OUTPUT_FRAC,
                )

                clear_value = 1 if index == 0 else 0

                writer.writerow([
                    clear_value,
                    a_code,
                    b_code,
                    expected
                ])

                total_vectors += 1

    print("RTL TEST VECTOR GENERATION")
    print("=" * 40)
    print(f"Input width         : {input_width}")
    print(f"Input frac          : {input_frac}")
    print(f"Accumulator width   : {acc_width}")
    print(f"Accumulator frac    : {acc_frac}")
    print(f"Output width        : {OUTPUT_WIDTH}")
    print(f"Output frac         : {OUTPUT_FRAC}")
    print(f"Number of sequences : {NUM_SEQUENCES}")
    print(f"Number of vectors   : {total_vectors}")
    print(f"Random seed         : {RANDOM_SEED}")
    print(f"Output file         : {OUTPUT_FILE}")
    print("Generation result   : PASS")


if __name__ == "__main__":
    main()