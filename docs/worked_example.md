# Independently checked worked example

All values below are hypothetical normalized priority ratings, with two alternatives and two criteria. Criterion weights are 0.4 and 0.6. For alternative A, the triangular ratings are (0.2, 0.4, 0.6) and (0.5, 0.7, 0.9). For alternative B, they are (0.7, 0.8, 0.9) and (0.1, 0.2, 0.3). This example checks the formulas and does not describe a crossing.

For A, the weighted numbers are (0.08, 0.16, 0.24) and (0.30, 0.42, 0.54). The positive ideal numbers are (0.4, 0.4, 0.4) and (0.6, 0.6, 0.6); both negative ideals are (0, 0, 0).

The vertex distances to the positive ideals are:

- Criterion 1: sqrt[(0.32² + 0.24² + 0.16²)/3] = 0.2487301081.
- Criterion 2: sqrt[(0.30² + 0.18² + 0.06²)/3] = 0.2049390153.

The vertex distances to the negative ideals are:

- Criterion 1: sqrt[(0.08² + 0.16² + 0.24²)/3] = 0.1728197520.
- Criterion 2: sqrt[(0.30² + 0.42² + 0.54²)/3] = 0.4312771731.

Summing across criteria gives D⁺ = 0.4536691234 and D⁻ = 0.6040969250. A's closeness is D⁻/(D⁺ + D⁻) = **0.5711063670**. The values are asserted independently in `tests/test_model.py`.

For a triangle (0.2, 0.4, 0.6), membership is zero outside [0.2, 0.6], rises linearly to one at 0.4, then falls linearly to zero at 0.6. Membership at 0.3 is 0.5. Membership expresses compatibility with the imprecise rating, not probability.
