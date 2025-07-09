---
title: Linear Algebra for ML
tags: [math, linear-algebra, ml]
created: 2023-01-25
---

# Linear Algebra for Machine Learning

Linear algebra is fundamental to understanding machine learning algorithms.

## Vectors

A vector is an ordered list of numbers representing magnitude and direction.

### Vector Operations
- **Addition**: v + w = [v₁ + w₁, v₂ + w₂, ...]
- **Scalar multiplication**: cv = [cv₁, cv₂, ...]
- **Dot product**: v·w = v₁w₁ + v₂w₂ + ...

## Matrices

A matrix is a rectangular array of numbers.

### Matrix Operations
- **Addition**: A + B (element-wise)
- **Multiplication**: AB (row × column)
- **Transpose**: A^T (rows become columns)
- **Inverse**: A^(-1) (if it exists)

## Applications in ML

### Linear Regression
- Uses matrix multiplication: y = Xβ + ε
- Normal equation: β = (X^T X)^(-1) X^T y

### Principal Component Analysis (PCA)
- Eigenvalue decomposition
- Dimensionality reduction
- Related to: [[Machine Learning Basics]]

### Neural Networks
- Weight matrices
- Forward propagation as matrix multiplication
- Backpropagation uses chain rule

#math #linearalgebra #ml #math51
