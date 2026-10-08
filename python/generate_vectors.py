import random
import csv


# ==========================================
# Configuration
# ==========================================

N = 100

random.seed(42)


# ==========================================
# Generate vectors
# ==========================================

with open(
    "vectors/test_vectors.csv",
    "w",
    newline=""
) as file:

    writer = csv.writer(file)


    # Header

    writer.writerow([
        "A",
        "B"
    ])


    # Data

    for _ in range(N):

        A = random.randint(
            -128,
            127
        )

        B = random.randint(
            -128,
            127
        )


        writer.writerow([
            A,
            B
        ])


print(
    f"Generated {N} test vectors."
)

print(
    "File: vectors/test_vectors.csv"
)
