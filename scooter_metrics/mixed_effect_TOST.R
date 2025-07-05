# Load necessary libraries
library(readr)  # For reading CSV files
library(lme4)   # For fitting linear mixed-effects models
library(lmerTest)  # For hypothesis testing with mixed models

# Set a seed for reproducibility
set.seed(0)

# Define equivalence bounds for the Two One-Sided Tests (TOST)
bound_u <- 0.2  # Upper equivalence bound
bound_l <- -0.2  # Lower equivalence bound

# Set the significance level for equivalence testing
alpha <- 0.05

# Print analysis description
cat("Performing TOST (Two One-Sided Tests) on a linear mixed-effects model.\n")
cat("Goal: Assess whether ratings for 'modified' and 'real' images are equivalent within ±0.2 bounds.\n")

# Read the dataset from a CSV file
attack <- read_csv("anonymized_cadv_4_6_with_image_ids.csv")

# Ensure categorical variables are correctly encoded as factors
attack$pid <- as.factor(attack$pid)  # Convert participant IDs to factor for random effects
attack$image_id <- as.factor(attack$image_id)  # Convert image IDs to factor for grouping
attack$image_type <- as.factor(attack$image_type)  # Ensure 'image_type' is a factor

# Fit a linear mixed-effects model:
# - Fixed effect: image_type (to compare real vs modified ratings)
# - Random effects:
#   - By-participant (pid): allows individual participants to have different intercepts/slopes
#   - By-image (image_id): accounts for variability in ratings due to different images
fm <- lmer(rating ~ image_type + (1 + image_type | pid) + (1 + image_type | image_id), data = attack)

# Check for singularity issues in the model
if (isSingular(fm, tol = 1e-4)) {
  cat("Warning: Model is singular. Consider simplifying the random effects structure.\n")
} else {
  cat("Model passed singularity check (not overfitted).\n")
}

# Perform equivalence tests for lower and upper bounds
# Lower bound: Test if the fixed effect of "image_type" is significantly greater than -0.2
lower <- contest1D(fm, c(0, 1), confint = TRUE, rhs = bound_l)

# Upper bound: Test if the fixed effect of "image_type" is significantly less than +0.2
upper <- contest1D(fm, c(0, 1), confint = TRUE, rhs = bound_u)

# Compute p-values for the lower and upper bound tests
# - pt() computes the cumulative probability under the t-distribution
lower_p <- pt(lower$`t value`, lower$df, lower.tail = FALSE)  # P-value for lower bound
upper_p <- pt(upper$`t value`, upper$df, lower.tail = TRUE)   # P-value for upper bound

# Display the fixed effect of "image_type" (difference between real and modified ratings)
cat("Fixed effect for 'image_type (real vs. modified)': ")
cat(fixef(fm)["image_typereal"], "\n")  # Extracts effect of real images compared to modified ones

# Report p-values for equivalence tests
cat("P-value for lower bound test (Δ < Δ_L): ", lower_p, "\n")
cat("P-value for upper bound test (Δ > Δ_U): ", upper_p, "\n")

# Decision rule: Both p-values must be below alpha (0.05) to conclude equivalence
if (lower_p < alpha && upper_p < alpha) {
  cat("Conclusion: The effect is statistically equivalent to zero within the specified bounds (±0.2).\n")
} else {
  cat("Conclusion: The effect is NOT statistically equivalent to zero within the specified bounds (±0.2).\n")
}